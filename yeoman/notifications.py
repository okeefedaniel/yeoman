"""
Yeoman notification type definitions.
Registered in YeomanConfig.ready().
"""
from keel.notifications.registry import NotificationType, register


YEOMAN_NOTIFICATION_TYPES = [
    NotificationType(
        key='invitation_received',
        label='New Invitation Received',
        description='A new invitation has been submitted via the public form.',
        category='Invitations',
        default_channels=['in_app', 'email'],
        default_roles=['yeoman_admin', 'yeoman_scheduler'],
    ),
    NotificationType(
        key='invitation_assigned',
        label='Invitation Assigned',
        description='An invitation has been assigned to you.',
        category='Invitations',
        default_channels=['in_app', 'email'],
    ),
    NotificationType(
        key='invitation_delegated',
        label='Invitation Delegated',
        description='An invitation has been delegated to you.',
        category='Invitations',
        default_channels=['in_app', 'email'],
    ),
    NotificationType(
        key='invitation_accepted',
        label='Invitation Accepted',
        description='Your invitation has been accepted.',
        category='Invitations',
        default_channels=['email'],
    ),
    NotificationType(
        key='invitation_declined',
        label='Invitation Declined',
        description='Your invitation has been declined.',
        category='Invitations',
        default_channels=['email'],
    ),
    NotificationType(
        key='invitation_scheduled',
        label='Invitation Scheduled',
        description='An invitation has been pushed to the calendar.',
        category='Invitations',
        default_channels=['in_app', 'email'],
    ),
    NotificationType(
        key='invitation_status_changed',
        label='Invitation Status Changed',
        description='The status of an invitation you are assigned to has changed.',
        category='Invitations',
        default_channels=['in_app'],
    ),
]


def register_notification_types():
    """Register all Yeoman notification types. Called from AppConfig.ready()."""
    for nt in YEOMAN_NOTIFICATION_TYPES:
        register(nt)
