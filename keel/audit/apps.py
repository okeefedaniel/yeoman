from django.apps import AppConfig


class KeelAuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'keel.audit'
    label = 'keel_audit'
    verbose_name = 'Keel Audit'
