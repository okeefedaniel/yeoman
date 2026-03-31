from keel.workflow.registry import register_workflow

YEOMAN_INVITATION_WORKFLOW = {
    'name': 'yeoman_invitation',
    'initial_state': 'received',
    'transitions': [
        {
            'name': 'start_review',
            'from': 'received',
            'to': 'under_review',
            'roles': ['yeoman_scheduler', 'yeoman_admin'],
        },
        {
            'name': 'request_info',
            'from': 'under_review',
            'to': 'needs_info',
            'roles': ['yeoman_scheduler', 'yeoman_admin'],
        },
        {
            'name': 'info_received',
            'from': 'needs_info',
            'to': 'under_review',
            'roles': ['yeoman_scheduler', 'yeoman_admin'],
        },
        {
            'name': 'accept',
            'from': 'under_review',
            'to': 'accepted',
            'roles': ['yeoman_admin'],
        },
        {
            'name': 'decline',
            'from': ['under_review', 'received'],
            'to': 'declined',
            'roles': ['yeoman_admin'],
        },
        {
            'name': 'delegate',
            'from': ['accepted', 'under_review'],
            'to': 'delegated',
            'roles': ['yeoman_admin'],
        },
        {
            'name': 'push_to_calendar',
            'from': ['accepted', 'delegated'],
            'to': 'scheduled',
            'roles': ['yeoman_scheduler', 'yeoman_admin'],
        },
        {
            'name': 'complete',
            'from': 'scheduled',
            'to': 'completed',
            'roles': ['yeoman_scheduler', 'yeoman_admin'],
        },
        {
            'name': 'cancel',
            'from': ['received', 'under_review', 'needs_info', 'accepted', 'delegated', 'scheduled'],
            'to': 'cancelled',
            'roles': ['yeoman_scheduler', 'yeoman_admin'],
        },
        {
            'name': 'reopen',
            'from': ['declined', 'cancelled'],
            'to': 'under_review',
            'roles': ['yeoman_admin'],
        },
    ],
}

# Status display metadata
STATUS_DISPLAY = {
    'received': {'label': 'Received', 'color': '#6c757d', 'bg': 'secondary', 'border': 'dashed'},
    'under_review': {'label': 'Under Review', 'color': '#0d6efd', 'bg': 'primary', 'border': 'dashed'},
    'needs_info': {'label': 'Needs Info', 'color': '#ffc107', 'bg': 'warning', 'border': 'dashed'},
    'accepted': {'label': 'Accepted', 'color': '#198754', 'bg': 'success', 'border': 'solid'},
    'declined': {'label': 'Declined', 'color': '#dc3545', 'bg': 'danger', 'border': 'solid'},
    'delegated': {'label': 'Delegated', 'color': '#20c997', 'bg': 'info', 'border': 'solid'},
    'scheduled': {'label': 'Scheduled', 'color': '#6f42c1', 'bg': 'purple', 'border': 'solid'},
    'completed': {'label': 'Completed', 'color': '#495057', 'bg': 'dark', 'border': 'solid'},
    'cancelled': {'label': 'Cancelled', 'color': '#e9967a', 'bg': 'secondary', 'border': 'solid'},
}

STATUS_COLORS = {k: v['color'] for k, v in STATUS_DISPLAY.items()}
STATUS_BORDERS = {k: v['border'] for k, v in STATUS_DISPLAY.items()}


def register_yeoman_workflow():
    """Called from YeomanConfig.ready()."""
    register_workflow(YEOMAN_INVITATION_WORKFLOW)
