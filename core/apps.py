from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    label = 'yeoman_core'
    verbose_name = 'Yeoman Core'

    def ready(self):
        # Register Yeoman models for signal-based audit logging
        from keel.core.audit_signals import register_audited_model, connect_audit_signals

        register_audited_model('yeoman.Invitation', 'Invitation')
        register_audited_model('yeoman.InvitationAttachment', 'Invitation Attachment')
        register_audited_model('yeoman.InvitationTag', 'Invitation Tag')
        register_audited_model('yeoman.PrincipalProfile', 'Principal Profile')
        register_audited_model('yeoman.ReferenceAddress', 'Reference Address')
        register_audited_model('yeoman.DelegationLog', 'Delegation Log')

        connect_audit_signals()
