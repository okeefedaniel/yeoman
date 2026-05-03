"""
Yeoman invitation workflow — powered by Keel WorkflowEngine.

Defines all valid status transitions, role requirements, and display metadata.
The WorkflowEngine auto-creates InvitationStatusHistory records on every
transition via the history_model parameter.
"""
from keel.core.workflow import Transition, WorkflowEngine

# ---------------------------------------------------------------------------
# Workflow engine
# ---------------------------------------------------------------------------
INVITATION_WORKFLOW = WorkflowEngine(
    transitions=[
        # Triage
        Transition('received', 'under_review', roles=['yeoman_scheduler', 'yeoman_admin'], label='Start Review'),
        Transition('under_review', 'needs_info', roles=['yeoman_scheduler', 'yeoman_admin'], label='Request Info'),
        Transition('needs_info', 'under_review', roles=['yeoman_scheduler', 'yeoman_admin'], label='Info Received'),

        # Decision
        Transition('under_review', 'accepted', roles=['yeoman_admin', 'yeoman_principal'], label='Accept'),
        Transition('under_review', 'tentative', roles=['yeoman_admin', 'yeoman_principal'], label='Mark Tentative'),
        Transition('under_review', 'declined', roles=['yeoman_admin', 'yeoman_principal'], label='Decline', require_comment=True),

        # Tentative → confirm or decline
        Transition('tentative', 'accepted', roles=['yeoman_admin', 'yeoman_principal'], label='Confirm'),
        Transition('tentative', 'declined', roles=['yeoman_admin', 'yeoman_principal'], label='Decline', require_comment=True),

        # Delegation (from accepted or tentative)
        Transition('accepted', 'delegated', roles=['yeoman_admin'], label='Delegate'),
        Transition('tentative', 'delegated', roles=['yeoman_admin'], label='Delegate'),

        # Scheduling (push to calendar)
        Transition('accepted', 'scheduled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Push to Calendar'),
        Transition('tentative', 'scheduled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Confirm & Schedule'),
        Transition('delegated', 'scheduled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Push to Calendar'),

        # Completion
        Transition('scheduled', 'completed', roles=['yeoman_scheduler', 'yeoman_admin'], label='Complete'),

        # Cancel from any active state
        Transition('received', 'cancelled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Cancel'),
        Transition('under_review', 'cancelled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Cancel'),
        Transition('needs_info', 'cancelled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Cancel'),
        Transition('accepted', 'cancelled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Cancel'),
        Transition('tentative', 'cancelled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Cancel'),
        Transition('delegated', 'cancelled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Cancel'),
        Transition('scheduled', 'cancelled', roles=['yeoman_scheduler', 'yeoman_admin'], label='Cancel'),

        # Reopen
        Transition('declined', 'under_review', roles=['yeoman_admin'], label='Reopen'),
        Transition('cancelled', 'under_review', roles=['yeoman_admin'], label='Reopen'),
    ],
    history_model='yeoman.InvitationStatusHistory',
    history_fk_field='invitation',
)


# ---------------------------------------------------------------------------
# Status display metadata (for templates)
# ---------------------------------------------------------------------------
STATUS_DISPLAY = {
    'received':     {'label': 'Received',     'color': '#6c757d', 'bg': 'secondary', 'border': 'dashed'},
    'under_review': {'label': 'Under Review', 'color': '#0d6efd', 'bg': 'primary',   'border': 'dashed'},
    'needs_info':   {'label': 'Needs Info',   'color': '#ffc107', 'bg': 'warning',    'border': 'dashed'},
    'accepted':     {'label': 'Accepted',     'color': '#198754', 'bg': 'success',    'border': 'solid'},
    'tentative':    {'label': 'Tentative',    'color': '#fd7e14', 'bg': 'warning',    'border': 'dashed'},
    'declined':     {'label': 'Declined',     'color': '#dc3545', 'bg': 'danger',     'border': 'solid'},
    'delegated':    {'label': 'Delegated',    'color': '#20c997', 'bg': 'info',       'border': 'solid'},
    'scheduled':    {'label': 'Scheduled',    'color': '#6f42c1', 'bg': 'purple',     'border': 'solid'},
    'completed':    {'label': 'Completed',    'color': '#495057', 'bg': 'dark',       'border': 'solid'},
    'cancelled':    {'label': 'Cancelled',    'color': '#e9967a', 'bg': 'secondary',  'border': 'solid'},
}

STATUS_COLORS = {k: v['color'] for k, v in STATUS_DISPLAY.items()}
STATUS_BORDERS = {k: v['border'] for k, v in STATUS_DISPLAY.items()}
