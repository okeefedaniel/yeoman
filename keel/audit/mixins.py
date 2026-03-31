from django.db import models


class AuditableMixin(models.Model):
    """
    Mixin that marks a model as auditable.
    In production keel.audit, this hooks into save/delete signals
    to create AuditLogEntry records automatically.
    Stub: just marks the model. Full audit logging is a TODO.
    """

    class Meta:
        abstract = True
