import logging

from .models import Notification

logger = logging.getLogger(__name__)


def notify(recipient, template_slug, context=None, channels=None):
    """
    Send a notification to a user. Stub implementation.

    In production keel.notifications, this:
    - Renders email templates
    - Sends emails via configured backend
    - Creates in-app notification records
    - Respects user digest preferences
    - Handles channel routing (email, in_app, push)
    """
    channels = channels or ['in_app']
    context = context or {}

    title = template_slug.replace('_', ' ').title()
    body = str(context)

    if 'in_app' in channels:
        Notification.objects.create(
            recipient=recipient,
            template_slug=template_slug,
            title=title,
            body=body,
            channel='in_app',
        )

    if 'email' in channels:
        logger.info(
            f"[NOTIFICATION] Email to {recipient.email}: "
            f"{template_slug} — {title}"
        )

    return True
