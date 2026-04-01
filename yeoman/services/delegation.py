import logging

from django.utils import timezone

from yeoman.models import DelegationLog

logger = logging.getLogger(__name__)


def delegate_invitation(invitation, delegated_by, delegated_to, notes=''):
    """Delegate an invitation to another user."""
    DelegationLog.objects.create(
        invitation=invitation,
        delegated_by=delegated_by,
        delegated_to=delegated_to,
        notes=notes,
    )

    invitation.delegated_to = delegated_to
    invitation.delegated_by = delegated_by
    invitation.delegated_at = timezone.now()
    invitation.delegation_notes = notes
    invitation.save()

    invitation.transition('delegate', user=delegated_by)

    # TODO: integrate with keel.notifications.dispatch when ready
    logger.info(
        "Invitation %s delegated from %s to %s",
        invitation.pk, delegated_by, delegated_to,
    )
