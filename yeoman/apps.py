from django.apps import AppConfig


class YeomanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'yeoman'
    verbose_name = 'Yeoman'

    def ready(self):
        from .workflow import register_yeoman_workflow
        register_yeoman_workflow()
