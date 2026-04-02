from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone

from keel.calendar.ical import generate_single_ical, ical_response
from yeoman.models import Invitation


def invitation_ical(request, pk):
    """Download a single invitation as an .ics file."""
    invitation = get_object_or_404(Invitation, pk=pk)

    start = timezone.make_aware(
        datetime.combine(invitation.event_date, invitation.event_time_start),
    ) if invitation.event_time_start else timezone.make_aware(
        datetime.combine(invitation.event_date, datetime.min.time()),
    )

    if invitation.event_time_end:
        end = timezone.make_aware(
            datetime.combine(invitation.event_date, invitation.event_time_end),
        )
    else:
        from datetime import timedelta
        end = start + timedelta(hours=1, minutes=30)

    location_parts = [invitation.venue_name, invitation.venue_city]
    location = ', '.join(p for p in location_parts if p)
    if not location and invitation.virtual_link:
        location = invitation.virtual_link

    ics = generate_single_ical(
        title=invitation.event_name,
        start=start,
        end=end,
        location=location,
        description=invitation.event_description,
        uid=str(invitation.pk),
    )

    filename = f'{invitation.event_name[:40].replace(" ", "_")}.ics'
    return ical_response(ics, filename=filename)
