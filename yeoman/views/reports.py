import csv
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, F, Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from yeoman.models import Invitation
from yeoman.workflow import STATUS_DISPLAY


class ReportsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'yeoman/reports_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Scope to caller's agency so cross-agency users don't see
        # aggregate volumes / submitter orgs they don't own. (CSO 2026-05-03)
        qs = Invitation.objects.for_user(self.request.user)

        # Date range filter — clamp to a sane range so a user can't
        # blow up the query planner with `days=99999999`.
        try:
            days = int(self.request.GET.get('days', 90))
        except (TypeError, ValueError):
            days = 90
        days = max(1, min(days, 3650))
        cutoff = timezone.now() - timedelta(days=days)
        qs_period = qs.filter(created_at__gte=cutoff)
        ctx['days'] = days

        # Volume by status
        ctx['by_status'] = list(
            qs_period.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Volume by format
        ctx['by_format'] = list(
            qs_period.values('event_format')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Volume by modality
        ctx['by_modality'] = list(
            qs_period.values('modality')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Top submitter organizations
        ctx['top_orgs'] = list(
            qs_period.exclude(submitter_organization='')
            .values('submitter_organization')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # Monthly volume (last 6 months)
        monthly = []
        now = timezone.now()
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1)
            else:
                month_end = now
            count = qs.filter(created_at__gte=month_start, created_at__lt=month_end).count()
            monthly.append({
                'month': month_start.strftime('%b %Y'),
                'count': count,
            })
        ctx['monthly_volume'] = monthly

        # Delegation rate
        total = qs_period.count()
        delegated = qs_period.filter(delegated_to__isnull=False).count()
        ctx['delegation_rate'] = round(delegated / total * 100) if total else 0
        ctx['total_period'] = total

        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        return ctx


class InvitationExportView(LoginRequiredMixin, View):
    """Export filtered invitations as CSV."""

    def get(self, request):
        # CSV export must respect the same agency scoping as the list
        # view — without ``for_user`` any logged-in user could dump
        # every invitation in the system as CSV. (CSO 2026-05-03)
        qs = Invitation.objects.for_user(request.user).select_related(
            'assigned_to', 'delegated_to', 'agency',
        )

        # Apply same filters as list view
        status = request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        priority = request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="yeoman_invitations.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Event Name', 'Event Date', 'Start Time', 'End Time',
            'Format', 'Modality', 'Status', 'Priority',
            'Submitter Name', 'Submitter Email', 'Organization',
            'Venue', 'City', 'State',
            'Expected Attendees', 'Press Expected', 'Recorded',
            'Surrogate OK', 'Assigned To', 'Delegated To',
            'Created', 'Updated',
        ])

        for inv in qs.order_by('-event_date'):
            writer.writerow([
                inv.event_name,
                inv.event_date,
                inv.event_time_start,
                inv.event_time_end or '',
                inv.get_event_format_display(),
                inv.get_modality_display(),
                inv.status,
                inv.priority,
                inv.submitter_name,
                inv.submitter_email,
                inv.submitter_organization,
                inv.venue_name,
                inv.venue_city,
                inv.venue_state,
                inv.expected_attendees or '',
                inv.press_expected,
                inv.will_be_recorded,
                'Yes' if inv.surrogate_ok else 'No',
                str(inv.assigned_to) if inv.assigned_to else '',
                str(inv.delegated_to) if inv.delegated_to else '',
                inv.created_at.strftime('%Y-%m-%d %H:%M'),
                inv.updated_at.strftime('%Y-%m-%d %H:%M'),
            ])

        return response
