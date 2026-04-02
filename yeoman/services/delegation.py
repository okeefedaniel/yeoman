import logging

from django.utils import timezone

from keel.notifications.dispatch import notify

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

    invitation.transition('delegated', user=delegated_by, comment=notes)

    notify(
        event='invitation_delegated',
        actor=delegated_by,
        recipients=[delegated_to],
        context={'invitation': invitation},
        title=str(invitation.event_name),
        link=f'/invitations/{invitation.pk}/',
    )

    logger.info(
        "Invitation %s delegated from %s to %s",
        invitation.pk, delegated_by, delegated_to,
    )
