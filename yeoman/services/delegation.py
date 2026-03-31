from django.utils import timezone

from keel.collaboration.services import add_comment
from keel.notifications.dispatch import notify

from yeoman.models import DelegationLog


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

    add_comment(
        invitation,
        delegated_by,
        f"Delegated to @{delegated_to.username}. {notes}".strip(),
    )

    notify(
        recipient=delegated_to,
        template_slug='yeoman_delegated_to_you',
        context={
            'invitation': str(invitation),
            'delegated_by': str(delegated_by),
            'notes': notes,
        },
        channels=['email', 'in_app'],
    )
