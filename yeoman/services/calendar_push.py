"""
Calendar push service for Yeoman.

Thin wrapper around keel.calendar that handles Invitation-specific logic.
"""
import logging
from datetime import datetime, timedelta

from django.utils import timezone

from keel.calendar import push_event, cancel_event

logger = logging.getLogger(__name__)


def push_invitation_to_calendar(invitation, user=None):
    """Push an accepted/delegated invitation to the external calendar.

    Args:
        invitation: Invitation model instance
        user: User performing the action (defaults to assigned_to)

    Returns:
        dict with keys: success, external_id, error, calendar_event_id
    """
    target_user = user or invitation.assigned_to or invitation.delegated_to
    if not target_user:
        return {
            'success': False,
            'external_id': '',
            'error': 'No user to push calendar event for',
            'calendar_event_id': None,
        }

    # Build start/end datetimes from invitation date + time fields
    start = timezone.make_aware(
        datetime.combine(invitation.event_date, invitation.event_time_start),
    )
    if invitation.event_time_end:
        end = timezone.make_aware(
            datetime.combine(invitation.event_date, invitation.event_time_end),
        )
    else:
        end = start + timedelta(minutes=90)

    # Build location string
    location_parts = [
        invitation.venue_name,
        invitation.venue_address,
        invitation.venue_city,
    ]
    location = ', '.join(p for p in location_parts if p)
    if not location and invitation.virtual_link:
        location = invitation.virtual_link

    result = push_event(
        event_type='invitation_scheduled',
        user=target_user,
        title=invitation.event_name,
        start=start,
        end=end,
        location=location,
        description=invitation.event_description,
        context={
            'invitation_id': str(invitation.pk),
            'submitter': invitation.submitter_name,
            'format': invitation.event_format,
            'modality': invitation.modality,
            'virtual_link': invitation.virtual_link,
        },
        content_object=invitation,
    )

    # Update denormalized fields on Invitation
    if result['success']:
        invitation.calendar_event_id = result['external_id']
        invitation.calendar_pushed_at = timezone.now()
        invitation.save(update_fields=['calendar_event_id', 'calendar_pushed_at'])

    return result


def cancel_invitation_calendar_event(invitation):
    """Cancel the calendar event linked to an invitation.

    Args:
        invitation: Invitation model instance

    Returns:
        dict with keys: success, error
    """
    if not invitation.calendar_event_id:
        return {'success': False, 'error': 'No calendar event to cancel'}

    # Find the CalendarEvent record by external_id
    try:
        from django.apps import apps
        from django.conf import settings
        EventModel = apps.get_model(settings.KEEL_CALENDAR_EVENT_MODEL)
        event = EventModel.objects.get(external_id=invitation.calendar_event_id)
        result = cancel_event(event.pk)
    except Exception as e:
        logger.warning("Could not find CalendarEvent for invitation %s: %s", invitation.pk, e)
        result = {'success': False, 'error': str(e)}

    if result['success']:
        invitation.calendar_event_id = ''
        invitation.calendar_pushed_at = None
        invitation.save(update_fields=['calendar_event_id', 'calendar_pushed_at'])

    return result
