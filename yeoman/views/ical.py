from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.html import escape as _html_escape

from keel.calendar.ical import generate_single_ical, ical_response
from yeoman.models import Invitation, InvitationNote
from yeoman.views.invitations import (
    MAX_EMAIL_RECIPIENTS,
    _email_rate_limited,
    _get_invitation_or_404,
)


def _build_ics(invitation):
    """Build an .ics string from an invitation. Returns None if date is missing."""
    if not invitation.event_date:
        return None

    if invitation.event_time_start:
        start = timezone.make_aware(
            datetime.combine(invitation.event_date, invitation.event_time_start),
        )
    else:
        start = timezone.make_aware(
            datetime.combine(invitation.event_date, datetime.min.time()),
        )

    if invitation.event_time_end:
        end = timezone.make_aware(
            datetime.combine(invitation.event_date, invitation.event_time_end),
        )
    else:
        end = start + timedelta(hours=1, minutes=30)

    location_parts = [invitation.venue_name, invitation.venue_city]
    location = ', '.join(p for p in location_parts if p)
    if not location and invitation.virtual_link:
        location = invitation.virtual_link

    return generate_single_ical(
        title=invitation.event_name,
        start=start,
        end=end,
        location=location,
        description=invitation.event_description,
        uid=str(invitation.pk),
    )


def invitation_ical(request, pk):
    """Download a single invitation as an .ics file.

    Requires either an authenticated, agency-scoped user OR a valid
    ``status_token`` query param. The raw pk is leaked via notification
    emails, so authenticating on pk alone would disclose a principal's
    schedule to anyone who received a link.
    """
    token = request.GET.get('token', '')
    if token:
        invitation = get_object_or_404(
            Invitation, pk=pk, status_token=token,
        )
    else:
        if not request.user.is_authenticated:
            raise Http404('invitation not found')
        invitation = _get_invitation_or_404(request.user, pk)
    ics = _build_ics(invitation)
    if not ics:
        messages.error(request, 'Cannot generate calendar invite — event date is not set.')
        return redirect('yeoman:invitation_detail', pk=pk)
    filename = f'{invitation.event_name[:40].replace(" ", "_")}.ics'
    return ical_response(ics, filename=filename)


@login_required
def invitation_send_calendar(request, pk):
    """Email a calendar invite (.ics) to specified recipients."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = _get_invitation_or_404(request.user, pk)
    raw_emails = request.POST.get('recipients', '')
    recipients = [e.strip() for e in raw_emails.replace(';', ',').split(',') if e.strip()]

    if not recipients:
        messages.error(request, 'At least one recipient email is required.')
        return redirect('yeoman:invitation_detail', pk=pk)

    if len(recipients) > MAX_EMAIL_RECIPIENTS:
        messages.error(
            request,
            f'Calendar invites cap at {MAX_EMAIL_RECIPIENTS} recipients per send.',
        )
        return redirect('yeoman:invitation_detail', pk=pk)

    if _email_rate_limited(request.user):
        messages.error(request, 'Email send limit reached. Try again later.')
        return redirect('yeoman:invitation_detail', pk=pk)

    ics = _build_ics(invitation)
    if not ics:
        messages.error(request, 'Cannot send calendar invite — event date is not set.')
        return redirect('yeoman:invitation_detail', pk=pk)

    from django.conf import settings as django_settings
    subject = f'Calendar Invite: {invitation.event_name}'
    body_lines = [
        f'You are invited to: {invitation.event_name}',
        f'Date: {invitation.event_date.strftime("%A, %B %d, %Y")}',
    ]
    if invitation.event_time_start:
        time_str = invitation.event_time_start.strftime('%I:%M %p')
        if invitation.event_time_end:
            time_str += f' - {invitation.event_time_end.strftime("%I:%M %p")}'
        body_lines.append(f'Time: {time_str}')
    if invitation.venue_name:
        body_lines.append(f'Location: {invitation.venue_name}')
        if invitation.venue_address:
            body_lines.append(f'         {invitation.venue_address}')
    if invitation.virtual_link:
        body_lines.append(f'Virtual: {invitation.virtual_link}')
    body_lines.append('')
    body_lines.append('A calendar invite is attached.')
    body = '\n'.join(body_lines)
    # Escape before \n → <br> so attacker-controlled invitation fields
    # (venue_name etc.) cannot inject HTML into the outgoing email.
    html_body = _html_escape(body).replace('\n', '<br>')

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=recipients,
            reply_to=[request.user.email] if request.user.email else [],
        )
        email.attach_alternative(
            f'<div style="font-family:sans-serif;line-height:1.6">{html_body}</div>',
            'text/html',
        )
        ics_request = ics.replace('METHOD:PUBLISH', 'METHOD:REQUEST')
        filename = f'{invitation.event_name[:40].replace(" ", "_")}.ics'
        email.attach(filename, ics_request, 'text/calendar; method=REQUEST')
        email.send()

        invitation.calendar_pushed_at = timezone.now()
        invitation.calendar_sent_to = ', '.join(recipients)
        invitation.calendar_sent_by = request.user
        invitation.save(update_fields=[
            'calendar_pushed_at', 'calendar_sent_to', 'calendar_sent_by', 'updated_at',
        ])

        InvitationNote.objects.create(
            invitation=invitation,
            author=request.user,
            content=f'Calendar invite sent to: {", ".join(recipients)}',
            is_internal=False,
        )
        messages.success(request, f'Calendar invite sent to {len(recipients)} recipient(s).')
    except Exception as e:
        messages.error(request, f'Failed to send calendar invite: {e}')

    return redirect('yeoman:invitation_detail', pk=pk)
