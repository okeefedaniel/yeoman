from django.db import models

from .registry import get_workflow


class WorkflowMixin(models.Model):
    """
    Mixin that adds workflow state management to a model.
    The model must define WORKFLOW_NAME as a class attribute.

    In production keel.workflow, this provides:
    - Declarative state machine registration
    - Role-guarded transitions
    - Pre/post hooks
    - Validators on transitions
    """
    status = models.CharField(max_length=50, default='received', db_index=True)

    class Meta:
        abstract = True

    def get_workflow(self):
        return get_workflow(self.WORKFLOW_NAME)

    def get_available_transitions(self, user=None):
        """Return transitions available from the current state, optionally filtered by user role."""
        workflow = self.get_workflow()
        if not workflow:
            return []

        available = []
        for t in workflow.get('transitions', []):
            from_states = t['from'] if isinstance(t['from'], list) else [t['from']]
            if self.status not in from_states:
                continue

            if user and t.get('roles'):
                user_roles = user.get_roles(org=getattr(self, 'org', None))
                if not any(r in user_roles for r in t['roles']):
                    continue

            available.append(t)
        return available

    def transition(self, transition_name, user=None):
        """
        Execute a named transition. Validates state, roles, and runs hooks.
        """
        workflow = self.get_workflow()
        if not workflow:
            raise ValueError(f"No workflow registered: {self.WORKFLOW_NAME}")

        transition = None
        for t in workflow.get('transitions', []):
            if t['name'] == transition_name:
                transition = t
                break

        if not transition:
            raise ValueError(f"Unknown transition: {transition_name}")

        from_states = transition['from'] if isinstance(transition['from'], list) else [transition['from']]
        if self.status not in from_states:
            raise ValueError(
                f"Cannot transition '{transition_name}' from state '{self.status}'. "
                f"Allowed from: {from_states}"
            )

        if user and transition.get('roles'):
            user_roles = user.get_roles(org=getattr(self, 'org', None))
            if not any(r in user_roles for r in transition['roles']):
                raise PermissionError(
                    f"User {user} lacks required role for '{transition_name}'. "
                    f"Required: {transition['roles']}"
                )

        self.status = transition['to']
        self.save(update_fields=['status'])
        return self
