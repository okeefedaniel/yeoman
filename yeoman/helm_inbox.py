"""Yeoman's /api/v1/helm-feed/inbox/ endpoint — per-user inbox.

Items where the requesting user is the gating dependency in Yeoman:
``Invitation`` rows where the user is the assigned coordinator (or the
principal/delegate) AND the invitation is in an open status (not yet
completed, declined, or cancelled). Plus the user's unread
notifications.

Conforms to the UserInbox shape in helm.dashboard.feed_contract.
Auth + cache + sub-resolution come from keel.feed.helm_inbox_view.
"""
from django.conf import settings
from django.db.models import Q
from keel.feed.views import helm_inbox_view

from .helm_feed import _product_url


# Statuses where the invitation still needs human attention. Anything
# not in this set is either terminal or doesn't require user action.
_OPEN_STATUSES = ['received', 'under_review', 'accepted']


@helm_inbox_view
def yeoman_helm_feed_inbox(request, user):
    from core.models import Notification

    from .models import Invitation

    base_url = _product_url().rstrip('/')

    items = []
    open_invites = (
        Invitation.objects
        .filter(
            Q(assigned_to=user) | Q(principal=user) | Q(delegated_to=user),
            status__in=_OPEN_STATUSES,
        )
        .order_by('event_date')[:50]
    )
    for inv in open_invites:
        # Decide the user's role for this invitation to color the title.
        if inv.assigned_to_id == user.id:
            role = 'Coordinate'
        elif inv.principal_id == user.id:
            role = 'Speak'
        else:
            role = 'Cover for'
        items.append({
            'id': str(inv.pk),
            'type': 'invitation',
            'title': f'{role}: {inv.event_name}',
            'deep_link': f'{base_url}/invitations/{inv.pk}/',
            'waiting_since': inv.created_at.isoformat() if getattr(inv, 'created_at', None) else '',
            'due_date': inv.event_date.isoformat() if inv.event_date else None,
            'priority': inv.priority if inv.priority in ('low', 'normal', 'high', 'urgent') else 'normal',
        })

    unread = (
        Notification.objects
        .filter(recipient=user, is_read=False)
        .order_by('-created_at')[:50]
    )
    notifications = []
    for n in unread:
        link = n.link or ''
        if link and base_url and link.startswith('/'):
            link = f'{base_url}{link}'
        notifications.append({
            'id': str(n.id),
            'title': n.title,
            'body': getattr(n, 'message', '') or '',
            'deep_link': link,
            'created_at': n.created_at.isoformat(),
            'priority': (n.priority or 'normal').lower(),
        })

    return {
        'product': getattr(settings, 'KEEL_PRODUCT_CODE', 'yeoman'),
        'product_label': getattr(settings, 'KEEL_PRODUCT_NAME', 'Yeoman'),
        'product_url': base_url,
        'user_sub': '',  # filled by decorator
        'items': items,
        'unread_notifications': notifications,
        'fetched_at': '',  # filled by decorator
    }
