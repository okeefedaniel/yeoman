from django.apps import AppConfig


class YeomanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'yeoman'
    verbose_name = 'Yeoman'

    def ready(self):
        from keel.calendar import register, CalendarEventType

        register(CalendarEventType(
            key='invitation_scheduled',
            label='Invitation Scheduled',
            description='Push accepted/delegated invitation to external calendar.',
            default_duration_minutes=90,
            title_template='{event_name}',
        ))
