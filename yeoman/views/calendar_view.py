from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import TemplateView

from yeoman.models import Invitation
from yeoman.workflow import STATUS_DISPLAY


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'yeoman/calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        return ctx


@login_required
def calendar_events_json(request):
    """Return invitation events as JSON for FullCalendar."""
    start = request.GET.get('start', '')
    end = request.GET.get('end', '')

    qs = Invitation.objects.exclude(status__in=('declined', 'cancelled'))
    if start:
        qs = qs.filter(event_date__gte=start[:10])
    if end:
        qs = qs.filter(event_date__lte=end[:10])

    events = []
    for inv in qs.select_related('assigned_to'):
        display = STATUS_DISPLAY.get(inv.status, {})
        events.append({
            'id': str(inv.pk),
            'title': inv.event_name,
            'start': f'{inv.event_date}T{inv.event_time_start}' if inv.event_time_start else str(inv.event_date),
            'end': f'{inv.event_date}T{inv.event_time_end}' if inv.event_time_end else None,
            'url': f'/invitations/{inv.pk}/',
            'color': display.get('color', '#6c757d'),
            'extendedProps': {
                'status': inv.status,
                'status_label': display.get('label', inv.status),
                'format': inv.get_event_format_display(),
                'submitter': inv.submitter_name,
                'assigned_to': str(inv.assigned_to) if inv.assigned_to else '',
            },
        })

    return JsonResponse(events, safe=False)
