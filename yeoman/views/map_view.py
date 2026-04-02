from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import TemplateView

from yeoman.models import Invitation
from yeoman.workflow import STATUS_DISPLAY


class MapView(LoginRequiredMixin, TemplateView):
    template_name = 'yeoman/map.html'


@login_required
def map_markers_json(request):
    """Return geocoded invitations as GeoJSON-like markers."""
    qs = (
        Invitation.objects
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .exclude(status__in=('declined', 'cancelled'))
        .select_related('assigned_to')
    )

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    markers = []
    for inv in qs:
        display = STATUS_DISPLAY.get(inv.status, {})
        markers.append({
            'id': str(inv.pk),
            'lat': float(inv.latitude),
            'lng': float(inv.longitude),
            'title': inv.event_name,
            'date': str(inv.event_date),
            'status': inv.status,
            'status_label': display.get('label', inv.status),
            'color': display.get('color', '#6c757d'),
            'venue': inv.venue_name,
            'format': inv.get_event_format_display(),
            'url': f'/invitations/{inv.pk}/',
        })

    return JsonResponse(markers, safe=False)
