"""External intake API for creating Invitations from dokeefect.com."""
import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone

from keel.accounts.models import Agency
from keel.notifications.dispatch import notify

from yeoman.api.auth import intake_api_view
from yeoman.api.serializers import InvitationIntakeSerializer
from yeoman.models import Invitation, PrincipalProfile

logger = logging.getLogger(__name__)


def _compute_distances(event_location, agency):
    """Compute distances from each ReferenceAddress to the event location.

    Uses Google Distance Matrix API. Returns a list of dicts:
        [{"label": "Home", "distance": "42.3 mi", "duration": "48 mins",
          "directions_url": "https://..."}, ...]

    Returns empty list if no profile/addresses or API key is missing.
    """
    # Skip entirely in demo mode — the intake endpoint is auth-bypassed
    # there, so unauthenticated attackers could otherwise burn Google
    # Distance Matrix budget by looping POSTs.
    if getattr(settings, 'DEMO_MODE', False):
        return []

    api_key = getattr(settings, 'GOOGLE_GEOCODING_API_KEY', '') or ''
    if not api_key or not event_location:
        return []

    try:
        profile = agency.principal_profile
    except PrincipalProfile.DoesNotExist:
        return []

    addresses = list(profile.addresses.all())
    if not addresses:
        return []

    results = []
    for addr in addresses:
        try:
            origin = urllib.parse.quote(addr.address)
            destination = urllib.parse.quote(event_location)
            cache_key = f'yeoman:dm:{addr.address}|{event_location}'
            cached = cache.get(cache_key)
            if cached is not None:
                results.append(cached)
                continue
            url = (
                f"https://maps.googleapis.com/maps/api/distancematrix/json"
                f"?units=imperial&origins={origin}&destinations={destination}&key={api_key}"
            )
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            element = data.get('rows', [{}])[0].get('elements', [{}])[0]
            if element.get('status') == 'OK':
                directions_url = (
                    f"https://www.google.com/maps/dir/?api=1"
                    f"&origin={origin}&destination={destination}"
                )
                entry = {
                    'label': addr.label,
                    'distance': element['distance']['text'],
                    'duration': element['duration']['text'],
                    'directions_url': directions_url,
                }
                # 24h cache on (origin, destination) pair
                cache.set(cache_key, entry, timeout=86400)
                results.append(entry)
            else:
                results.append({
                    'label': addr.label,
                    'error': element.get('status', 'UNKNOWN'),
                })
        except Exception as e:
            logger.warning('Distance calc failed for %s: %s', addr.label, e)
            results.append({
                'label': addr.label,
                'error': str(e),
            })

    return results


@intake_api_view('YEOMAN_INTAKE_API_KEY')
def invitation_intake(request):
    """Create an Invitation from an external form submission.

    POST /api/v1/intake/invitation/
    Authorization: Bearer <YEOMAN_INTAKE_API_KEY>
    Content-Type: application/json
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    serializer = InvitationIntakeSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'errors': serializer.errors}, status=400)

    d = serializer.validated_data

    # Resolve agency (first active, matching PublicInviteView pattern)
    agency = Agency.objects.filter(is_active=True).first()
    if not agency:
        agency = Agency.objects.create(name='Default Agency', abbreviation='DEFAULT')

    # event_name / event_date / event_time_start are intentionally
    # optional. Leave event_name blank here — Invitation.save() fills a
    # derived default so the list view has something to show. Dates
    # are left as NULL when not provided; detail/list views render "TBD".
    invitation = Invitation(
        agency=agency,
        status='received',
        # Submitter
        submitter_first_name=d['first_name'],
        submitter_last_name=d.get('last_name', ''),
        submitter_email=d['email'],
        submitter_organization=d.get('organization', ''),
        # Event
        event_name=d.get('event_name', ''),
        event_date=d.get('event_date'),
        event_time_start=d.get('start_time'),
        event_time_end=d.get('end_time'),
        event_format=d['event_type'],  # already normalised by serializer
        modality=d['event_format'],    # already normalised by serializer
        # Location (geocoding happens in model.save())
        venue_address=d.get('location', ''),
        # Logistics
        expected_attendees=d.get('attendees'),
        surrogate_ok=d['proxy'],  # bool from serializer
        press_expected=d['press'],
        will_be_recorded=d['event_recorded'],
        # Notes
        event_description=d.get('notes', ''),
    )
    invitation.save()

    # Notify admins/schedulers (same as PublicInviteView). Fall back to
    # is_staff users if no user holds a yeoman_admin / yeoman_scheduler
    # role — a successful intake that produces zero notifications is the
    # worst possible outcome (the work item exists but no one knows).
    User = get_user_model()
    role_recipients = list(
        User.objects.filter(
            is_active=True,
            product_access__product='yeoman',
            product_access__role__in=['yeoman_admin', 'yeoman_scheduler'],
            product_access__is_active=True,
        ).distinct()
    )
    if not role_recipients:
        fallback = list(User.objects.filter(is_active=True, is_staff=True))
        if fallback:
            logger.warning(
                'No yeoman_admin/yeoman_scheduler users for invitation %s; '
                'falling back to %d is_staff users',
                invitation.pk, len(fallback),
            )
        else:
            logger.error(
                'No notification recipients for invitation %s '
                '(no admins, no staff users)', invitation.pk,
            )
        recipients = fallback
    else:
        recipients = role_recipients

    result = notify(
        event='invitation_received',
        recipients=recipients,
        context={'invitation': invitation},
        title=str(invitation.event_name),
        message=f'New invitation from {invitation.submitter_name} ({invitation.submitter_organization}) via dokeefect.com.',
        link=f'/invitations/{invitation.pk}/',
    )
    logger.info(
        'Intake API created invitation %s from %s '
        '(notify: sent=%s skipped=%s errors=%s)',
        invitation.pk, d['email'],
        result['sent'], result['skipped'], result['errors'],
    )

    # Compute distances from reference addresses (non-blocking — errors don't fail the request)
    distances = _compute_distances(d.get('location', ''), agency)

    response = {
        'id': str(invitation.pk),
        'status': invitation.status,
        'status_token': str(invitation.status_token),
    }
    if distances:
        response['distances'] = distances

    return JsonResponse(response, status=201)
