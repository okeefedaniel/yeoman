from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from yeoman.models import Invitation
from yeoman.workflow import STATUS_DISPLAY

TERMINAL_STATUSES = ('completed', 'declined', 'cancelled')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'yeoman/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Invitation.objects.all()
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        user = self.request.user

        # Status counts
        counts = qs.values('status').annotate(count=Count('id'))
        status_counts = {row['status']: row['count'] for row in counts}
        ctx['status_counts'] = status_counts
        ctx['total_count'] = sum(status_counts.values())
        ctx['needs_attention'] = (
            status_counts.get('received', 0)
            + status_counts.get('needs_info', 0)
        )
        ctx['active_count'] = sum(
            status_counts.get(s, 0)
            for s in ('under_review', 'accepted', 'tentative', 'delegated', 'scheduled')
        )
        ctx['tentative_count'] = status_counts.get('tentative', 0)

        # Unassigned (claimable)
        ctx['unassigned_count'] = qs.filter(
            assigned_to__isnull=True,
        ).exclude(status__in=TERMINAL_STATUSES).count()

        # My assignments
        ctx['my_assignments'] = (
            qs.filter(assigned_to=user)
            .exclude(status__in=TERMINAL_STATUSES)
            .select_related('agency')
            .order_by('event_date')[:10]
        )
        ctx['my_assignment_count'] = (
            qs.filter(assigned_to=user)
            .exclude(status__in=TERMINAL_STATUSES)
            .count()
        )

        # My delegations
        ctx['my_delegations'] = (
            qs.filter(delegated_to=user)
            .exclude(status__in=TERMINAL_STATUSES)
            .select_related('agency')
            .order_by('event_date')[:10]
        )

        # Recent invitations
        ctx['recent_invitations'] = (
            qs.select_related('assigned_to')
            .order_by('-created_at')[:10]
        )

        # Upcoming events (next 7 days)
        ctx['upcoming_events'] = (
            qs.filter(event_date__gte=today, event_date__lte=next_week)
            .exclude(status__in=TERMINAL_STATUSES)
            .order_by('event_date', 'event_time_start')[:5]
        )

        # Overdue: past event date but not terminal
        ctx['overdue_count'] = qs.filter(
            event_date__lt=today,
        ).exclude(
            status__in=TERMINAL_STATUSES,
        ).count()

        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        return ctx
