from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView

from yeoman.forms import InvitationStaffForm
from yeoman.models import Invitation
from yeoman.workflow import STATUS_DISPLAY


class InvitationListView(LoginRequiredMixin, ListView):
    model = Invitation
    template_name = 'yeoman/invitation_list.html'
    context_object_name = 'invitations'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('assigned_to', 'agency')
        # Filters
        status = self.request.GET.get('status')
        if status:
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
            'assigned_to', 'delegated_to', 'delegated_by', 'agency', 'created_by',
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
        return ctx


class InvitationUpdateView(LoginRequiredMixin, UpdateView):
    model = Invitation
    form_class = InvitationStaffForm
    template_name = 'yeoman/invitation_detail.html'

    def get_success_url(self):
        return reverse('yeoman:invitation_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Invitation updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inv = self.object
        ctx['invitation'] = inv
        ctx['transitions'] = inv.get_available_transitions(self.request.user)
        ctx['delegation_history'] = inv.delegation_history.select_related(
            'delegated_by', 'delegated_to',
        )[:20]
        ctx['attachments'] = inv.attachments.all()
        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        return ctx


@login_required
def invitation_transition(request, pk):
    """Handle workflow transition POST."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    invitation = get_object_or_404(Invitation, pk=pk)
    transition_name = request.POST.get('transition')

    try:
        invitation.transition(transition_name, user=request.user)
        label = transition_name.replace('_', ' ').title()
        messages.success(request, f'Invitation transitioned: {label}')
    except (ValueError, PermissionError) as e:
        messages.error(request, str(e))

    return redirect('yeoman:invitation_detail', pk=pk)


@login_required
def invitation_delegate(request, pk):
    """Handle delegation POST."""
    if request.method != 'POST':
        return redirect('yeoman:invitation_detail', pk=pk)

    from yeoman.services.delegation import delegate_invitation
    from core.models import User

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
