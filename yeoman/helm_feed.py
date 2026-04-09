"""Yeoman's /api/v1/helm-feed/ endpoint.

Exposes scheduling metrics for Helm's executive dashboard.
"""
from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from keel.feed.views import helm_feed_view


def _product_url():
    if getattr(settings, 'DEMO_MODE', False):
        return 'https://demo-yeoman.docklabs.ai'
    return 'https://yeoman.docklabs.ai'


@helm_feed_view
def yeoman_helm_feed(request):
    from yeoman.models import Invitation

    now = timezone.now()
    base_url = _product_url()

    # ── Metrics ──────────────────────────────────────────────────

    # Pending invitations (received, not yet triaged)
    pending = Invitation.objects.filter(
        status='received',
    ).count()

    # This week's meetings (accepted invitations with event_date this week)
    week_start = now.date()
    week_end = week_start + timedelta(days=7)
    meetings_this_week = Invitation.objects.filter(
        status='accepted',
        event_date__gte=week_start,
        event_date__lte=week_end,
    ).count()

    # Triage backlog (received invitations older than 2 days)
    triage_backlog = Invitation.objects.filter(
        status='received',
        created_at__lt=now - timedelta(days=2),
    ).count()

    # Upcoming (next 30 days)
    upcoming_count = Invitation.objects.filter(
        status='accepted',
        event_date__gte=now.date(),
        event_date__lte=now.date() + timedelta(days=30),
    ).count()

    metrics = [
        {
            'key': 'pending_invitations',
            'label': 'Pending Invitations',
            'value': pending,
            'unit': None,
            'trend': None, 'trend_value': None, 'trend_period': None,
            'severity': 'normal',
            'deep_link': f'{base_url}/invitations/?status=received',
        },
        {
            'key': 'meetings_this_week',
            'label': 'Meetings This Week',
            'value': meetings_this_week,
            'unit': None,
            'trend': None, 'trend_value': None, 'trend_period': None,
            'severity': 'normal',
            'deep_link': f'{base_url}/calendar/',
        },
        {
            'key': 'triage_backlog',
            'label': 'Triage Backlog',
            'value': triage_backlog,
            'unit': None,
            'trend': None, 'trend_value': None, 'trend_period': None,
            'severity': 'warning' if triage_backlog > 3 else 'normal',
            'deep_link': f'{base_url}/invitations/?status=received',
        },
    ]

    # ── Action Items ─────────────────────────────────────────────
    action_items = []

    # Invitations needing triage
    needs_triage = (
        Invitation.objects
        .filter(status='received')
        .order_by('event_date', 'created_at')[:5]
    )
    for inv in needs_triage:
        action_items.append({
            'id': f'yeoman-triage-{inv.pk}',
            'type': 'review',
            'title': f'Triage: {inv.event_name[:80]}',
            'description': f'Event: {inv.event_date.strftime("%b %d") if inv.event_date else "TBD"}',
            'priority': 'medium' if not inv.event_date or inv.event_date > now.date() + timedelta(days=3) else 'high',
            'due_date': inv.event_date.isoformat() if inv.event_date else '',
            'assigned_to_role': 'scheduler',
            'deep_link': f'{base_url}/invitations/{inv.pk}/',
            'created_at': inv.created_at.isoformat() if inv.created_at else '',
        })

    # ── Alerts ───────────────────────────────────────────────────
    alerts = []

    if triage_backlog > 0:
        alerts.append({
            'id': 'yeoman-triage-backlog',
            'type': 'overdue',
            'title': f'{triage_backlog} invitation{"s" if triage_backlog != 1 else ""} awaiting triage for 2+ days',
            'severity': 'warning',
            'since': '',
            'deep_link': f'{base_url}/invitations/?status=received',
        })

    return {
        'product': 'yeoman',
        'product_label': 'Yeoman',
        'product_url': f'{base_url}/dashboard/',
        'metrics': metrics,
        'action_items': action_items,
        'alerts': alerts,
        'sparklines': {},
    }
