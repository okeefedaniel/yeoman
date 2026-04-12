"""External intake API for creating Invitations from dokeefect.com."""
import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings
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
                results.append({
                    'label': addr.label,
                    'distance': element['distance']['text'],
                    'duration': element['duration']['text'],
                    'directions_url': directions_url,
                })
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

    # Build event name from submitter + org if not provided
    event_name = d.get('event_name') or ''
    if not event_name:
        parts = [f"{d['first_name']} {d['last_name']}"]
        if d.get('organization'):
            parts.append(f"@ {d['organization']}")
        event_name = ' '.join(parts)

    invitation = Invitation(
        agency=agency,
        status='received',
        # Submitter
        submitter_first_name=d['first_name'],
        submitter_last_name=d['last_name'],
        submitter_email=d['email'],
        submitter_organization=d.get('organization', ''),
        # Event
        event_name=event_name,
        event_date=d.get('event_date') or timezone.now().date(),
        event_time_start=d.get('start_time') or timezone.now().time().replace(second=0, microsecond=0),
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

    # Notify admins/schedulers (same as PublicInviteView)
    notify(
        event='invitation_received',
        context={'invitation': invitation},
        title=str(invitation.event_name),
        message=f'New invitation from {invitation.submitter_name} ({invitation.submitter_organization}) via dokeefect.com.',
        link=f'/invitations/{invitation.pk}/',
    )

    logger.info('Intake API created invitation %s from %s', invitation.pk, d['email'])

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
