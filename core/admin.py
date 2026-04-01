from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Agency, AuditLog, CalendarEvent, Notification, NotificationPreference, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Yeoman', {'fields': ('role', 'title', 'phone', 'organization_name')}),
    )


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('abbreviation', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'abbreviation')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity_type', 'entity_id', 'user', 'timestamp')
    list_filter = ('action', 'entity_type', 'timestamp')
    readonly_fields = [f.name for f in AuditLog._meta.get_fields() if hasattr(f, 'name')]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'priority', 'is_read', 'created_at')
    list_filter = ('priority', 'is_read')
    readonly_fields = [f.name for f in Notification._meta.get_fields() if hasattr(f, 'name')]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'channel_in_app', 'channel_email', 'is_muted')
    list_filter = ('notification_type', 'is_muted')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event_type', 'provider', 'status', 'start_time', 'last_synced_at')
    list_filter = ('provider', 'status', 'event_type')
    search_fields = ('title', 'external_id')
    readonly_fields = ('id', 'external_id', 'status', 'sync_error', 'last_synced_at', 'created_at', 'updated_at')
