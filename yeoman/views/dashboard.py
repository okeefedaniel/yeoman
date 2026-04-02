from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from yeoman.models import Invitation
from yeoman.workflow import STATUS_DISPLAY


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'yeoman/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Invitation.objects.all()
        today = timezone.now().date()
        next_week = today + timedelta(days=7)

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
            for s in ('under_review', 'accepted', 'delegated', 'scheduled')
        )

        # Recent invitations
        ctx['recent_invitations'] = (
            qs.select_related('assigned_to')
            .order_by('-created_at')[:10]
        )

        # Upcoming events (next 7 days)
        ctx['upcoming_events'] = (
            qs.filter(event_date__gte=today, event_date__lte=next_week)
            .exclude(status__in=('declined', 'cancelled'))
            .order_by('event_date', 'event_time_start')[:5]
        )

        # Overdue: past event date but not completed/declined/cancelled
        ctx['overdue_count'] = qs.filter(
            event_date__lt=today,
        ).exclude(
            status__in=('completed', 'declined', 'cancelled'),
        ).count()

        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        return ctx
