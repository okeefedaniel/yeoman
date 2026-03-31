from django.apps import AppConfig


class KeelAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'keel.auth'
    label = 'keel_auth'
    verbose_name = 'Keel Auth'
