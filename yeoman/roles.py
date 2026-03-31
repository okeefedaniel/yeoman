"""
RBAC role definitions for Yeoman.
Registered with keel.auth. Each role is scoped to an Organization.
"""

YEOMAN_ROLES = [
    {
        'name': 'yeoman_admin',
        'description': (
            'Principal or chief scheduler. All transitions, all CRUD, '
            'manage users, configure tags, delegate.'
        ),
    },
    {
        'name': 'yeoman_scheduler',
        'description': (
            'Scheduling staff. Start review, request info, push to calendar, '
            'complete, cancel. Cannot accept/decline/delegate.'
        ),
    },
    {
        'name': 'yeoman_viewer',
        'description': (
            'Read-only staff. View invitations, calendar, map. '
            'Comment on threads. Cannot change status or assignment.'
        ),
    },
    {
        'name': 'yeoman_delegate',
        'description': (
            'Person an invitation is delegated to. View their delegated '
            'invitations only. Can comment. Can mark attendance.'
        ),
    },
]


def ensure_roles():
    """Create Yeoman roles if they don't exist. Idempotent."""
    from keel.auth.models import Role

    for role_def in YEOMAN_ROLES:
        Role.objects.get_or_create(
            name=role_def['name'],
            defaults={'description': role_def['description']},
        )
