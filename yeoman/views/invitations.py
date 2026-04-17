from itertools import chain
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView

from keel.notifications.dispatch import notify

from yeoman.forms import InvitationStaffForm
from yeoman.models import Invitation, InvitationNote
from yeoman.workflow import STATUS_DISPLAY

# Map target status to notification event key
STATUS_NOTIFICATIONS = {
    'accepted': 'invitation_accepted',
    'tentative': 'invitation_status_changed',
    'declined': 'invitation_declined',
    'scheduled': 'invitation_scheduled',
    'delegated': 'invitation_delegated',
    'under_review': 'invitation_status_changed',
    'needs_info': 'invitation_status_changed',
    'completed': 'invitation_status_changed',
    'cancelled': 'invitation_status_changed',
}


class InvitationListView(LoginRequiredMixin, ListView):
    model = Invitation
    template_name = 'yeoman/invitation_list.html'
    context_object_name = 'invitations'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('assigned_to', 'principal', 'agency')
        # Filters
        filter_type = self.request.GET.get('filter')
        if filter_type == 'overdue':
            from datetime import date
            from yeoman.views.dashboard import TERMINAL_STATUSES
            qs = qs.filter(event_date__lt=date.today()).exclude(
                status__in=TERMINAL_STATUSES,
            )
        status = self.request.GET.get('status')
        if status == 'needs_attention':
            qs = qs.filter(status__in=('received', 'needs_info'))
        elif status:
            qs = qs.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        fmt = self.request.GET.get('format')
        if fmt:
            qs = qs.filter(event_format=fmt)
        modality = self.request.GET.get('modality')
        if modality:
            qs = qs.filter(modality=modality)
        # Special filters
        assigned = self.request.GET.get('assigned')
        if assigned == 'me':
            qs = qs.filter(assigned_to=self.request.user)
        elif assigned == 'unassigned':
            qs = qs.filter(assigned_to__isnull=True).exclude(
                status__in=('declined', 'cancelled', 'completed'),
            )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(event_name__icontains=q)
                | Q(submitter_first_name__icontains=q)
                | Q(submitter_last_name__icontains=q)
                | Q(submitter_email__icontains=q)
                | Q(submitter_organization__icontains=q)
            )

        # Sorting
        sort = self.request.GET.get('sort', '-event_date')
        allowed = {
            'event_name', '-event_name',
            'event_date', '-event_date',
            'status', '-status',
            'priority', '-priority',
            'created_at', '-created_at',
        }
        if sort in allowed:
            qs = qs.order_by(sort)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = [('', 'All Statuses')] + [
            (k, v['label']) for k, v in STATUS_DISPLAY.items()
        ]
        ctx['priority_choices'] = [('', 'All Priorities')] + list(Invitation.PRIORITY_CHOICES)
        ctx['format_choices'] = [('', 'All Formats')] + list(Invitation.FORMAT_CHOICES)
        ctx['modality_choices'] = [('', 'All Modalities')] + list(Invitation.MODALITY_CHOICES)
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['current_priority'] = self.request.GET.get('priority', '')
        ctx['current_format'] = self.request.GET.get('format', '')
        ctx['current_modality'] = self.request.GET.get('modality', '')
        ctx['current_assigned'] = self.request.GET.get('assigned', '')
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_sort'] = self.request.GET.get('sort', '-event_date')
        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY

        # Build filter params for pagination links
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['filter_params'] = params.urlencode()
        return ctx


class InvitationDetailView(LoginRequiredMixin, DetailView):
    model = Invitation
    template_name = 'yeoman/invitation_detail.html'
    context_object_name = 'invitation'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'assigned_to', 'principal', 'delegated_to', 'delegated_by',
            'agency', 'created_by', 'calendar_sent_by',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inv = self.object
        ctx['transitions'] = inv.get_available_transitions(self.request.user)
        ctx['delegation_history'] = inv.delegation_history.select_related(
            'delegated_by', 'delegated_to',
        )[:20]
        ctx['attachments'] = inv.attachments.all()
        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        ctx['form'] = InvitationStaffForm(instance=inv)

        from yeoman.services import beacon
        from yeoman.models import PrincipalProfile
        ctx['beacon_available'] = beacon.is_available()

        # Pre-fill calendar invite recipients with principal + submitter
        suggested = []
        try:
            profile = inv.agency.principal_profile
            if profile.email:
                suggested.append(profile.email)
        except PrincipalProfile.DoesNotExist:
            pass
        if inv.submitter_email and inv.submitter_email not in suggested:
            suggested.append(inv.submitter_email)
        ctx['calendar_suggested_recipients'] = ', '.join(suggested)
        ctx['can_send_calendar'] = bool(inv.event_date)

        # Build unified timeline from status history + notes
        history = list(inv.status_history.select_related('changed_by').all())
        notes = list(inv.notes.select_related('author').all())
        delegations = list(inv.delegation_history.select_related(
            'delegated_by', 'delegated_to',
        ).all())

        # Normalize timeline entries with (timestamp, type, object)
        timeline = []
        for h in history:
            timeline.append({'timestamp': h.changed_at, 'type': 'status', 'obj': h})
        for n in notes:
            timeline.append({'timestamp': n.created_at, 'type': 'note', 'obj': n})
        for d in delegations:
            timeline.append({'timestamp': d.created_at, 'type': 'delegation', 'obj': d})
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        ctx['timeline'] = timeline

        return ctx


class InvitationUpdateView(LoginRequiredMixin, UpdateView):
    model = Invitation
    form_class = InvitationStaffForm
    template_name = 'yeoman/invitation_edit.html'

    def get_success_url(self):
        return reverse('yeoman:invitation_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Invitation updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['invitation'] = self.object
        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        return ctx


@login_required
def invitation_transition(request, pk):
    """Handle workflow transition POST.

    Expects POST data:
        target_status — the status to transition to
        comment — optional comment (required for some transitions like decline)
    """
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = get_object_or_404(Invitation, pk=pk)
    target_status = request.POST.get('target_status')
    comment = request.POST.get('comment', '').strip()

    try:
        transition = invitation.transition(target_status, user=request.user, comment=comment)
        messages.success(request, f'Invitation transitioned: {transition.label}')

        # Dispatch notification
        event_key = STATUS_NOTIFICATIONS.get(target_status)
        if event_key:
            recipients = [
                u for u in [invitation.assigned_to, invitation.delegated_to]
                if u is not None
            ]
            notify(
                event=event_key,
                actor=request.user,
                recipients=recipients or None,
                context={'invitation': invitation},
                title=str(invitation.event_name),
                link=f'/invitations/{invitation.pk}/',
            )
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))

    return redirect('yeoman:invitation_detail', pk=pk)


@login_required
def invitation_claim(request, pk):
    """Claim an unassigned invitation."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = get_object_or_404(Invitation, pk=pk)

    if invitation.assigned_to is not None:
        messages.warning(request, 'This invitation is already assigned.')
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation.assigned_to = request.user
    invitation.save(update_fields=['assigned_to', 'updated_at'])

    InvitationNote.objects.create(
        invitation=invitation,
        author=request.user,
        content=f'Claimed by {request.user.get_full_name() or request.user.username}',
    )

    messages.success(request, 'Invitation claimed.')
    return redirect('yeoman:invitation_detail', pk=pk)


@login_required
def invitation_unclaim(request, pk):
    """Release assignment on an invitation."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = get_object_or_404(Invitation, pk=pk)
    old_assignee = invitation.assigned_to

    invitation.assigned_to = None
    invitation.save(update_fields=['assigned_to', 'updated_at'])

    InvitationNote.objects.create(
        invitation=invitation,
        author=request.user,
        content=f'Released by {request.user.get_full_name() or request.user.username}',
    )

    messages.success(request, 'Assignment released.')
    return redirect('yeoman:invitation_detail', pk=pk)


@login_required
def invitation_add_note(request, pk):
    """Add an internal note to an invitation."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = get_object_or_404(Invitation, pk=pk)
    content = request.POST.get('content', '').strip()

    if not content:
        messages.error(request, 'Note content cannot be empty.')
        return redirect('yeoman:invitation_detail', pk=pk)

    InvitationNote.objects.create(
        invitation=invitation,
        author=request.user,
        content=content,
        is_internal=True,
    )

    messages.success(request, 'Note added.')
    return redirect('yeoman:invitation_detail', pk=pk)


@login_required
def invitation_beacon_toggle(request, pk):
    """Mark this invitation's submitter as added-to / skipped-from Beacon.

    POST ``decision`` = ``added`` | ``declined`` | ``reset``. On the first
    transition to ``added`` we push the contact to Beacon; subsequent
    flips just update local state (no duplicate push — Beacon's intake
    dedups by email anyway).
    """
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    from django.utils import timezone
    from yeoman.services import beacon

    if not beacon.is_available():
        messages.error(request, 'Beacon integration is not configured.')
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = get_object_or_404(Invitation, pk=pk)
    decision = request.POST.get('decision', '')

    if decision == 'added':
        if not invitation.beacon_contact_id:
            try:
                invitation.beacon_contact_id = beacon.push_invitation(invitation) or ''
            except Exception as e:
                messages.error(request, f'Beacon push failed: {e}')
                return redirect('yeoman:invitation_detail', pk=pk)
        invitation.beacon_status = 'added'
        messages.success(request, 'Submitter added to Beacon.')
    elif decision == 'declined':
        invitation.beacon_status = 'declined'
        messages.success(request, 'Marked as skipped for Beacon.')
    elif decision == 'reset':
        invitation.beacon_status = ''
        messages.success(request, 'Beacon decision cleared.')
    else:
        messages.error(request, 'Unknown decision.')
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation.beacon_decided_at = timezone.now()
    invitation.beacon_decided_by = request.user
    invitation.save(update_fields=[
        'beacon_status', 'beacon_contact_id',
        'beacon_decided_at', 'beacon_decided_by', 'updated_at',
    ])
    return redirect('yeoman:invitation_detail', pk=pk)


@login_required
def invitation_send_email(request, pk):
    """Send an email to the invitation submitter and log it as a note."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = get_object_or_404(Invitation, pk=pk)
    subject = request.POST.get('subject', '').strip()
    body = request.POST.get('body', '').strip()

    if not subject or not body:
        messages.error(request, 'Both subject and message are required.')
        return redirect('yeoman:invitation_detail', pk=pk)

    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings as django_settings

    from_email = django_settings.DEFAULT_FROM_EMAIL
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[invitation.submitter_email],
            reply_to=[request.user.email] if request.user.email else [],
        )
        html_body = body.replace('\n', '<br>')
        email.attach_alternative(
            f'<div style="font-family:sans-serif;line-height:1.5">{html_body}</div>',
            'text/html',
        )
        email.send()

        InvitationNote.objects.create(
            invitation=invitation,
            author=request.user,
            content=f'Email sent to {invitation.submitter_email}\nSubject: {subject}\n\n{body}',
            is_internal=False,
        )
        messages.success(request, f'Email sent to {invitation.submitter_email}.')
    except Exception as e:
        messages.error(request, f'Email failed: {e}')

    return redirect('yeoman:invitation_detail', pk=pk)


@login_required
def invitation_delegate(request, pk):
    """Handle delegation POST."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    from yeoman.services.delegation import delegate_invitation
    from django.contrib.auth import get_user_model
    User = get_user_model()

    invitation = get_object_or_404(Invitation, pk=pk)
    delegate_id = request.POST.get('delegate_to')
    notes = request.POST.get('notes', '')

    try:
        delegate_user = User.objects.get(pk=delegate_id)
        delegate_invitation(invitation, request.user, delegate_user, notes)
        messages.success(request, f'Delegated to {delegate_user}.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    except (ValueError, PermissionError) as e:
        messages.error(request, str(e))

    return redirect('yeoman:invitation_detail', pk=pk)
