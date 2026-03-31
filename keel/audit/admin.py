from django.contrib import admin

from .models import AuditLogEntry


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = ('action', 'content_type', 'object_id', 'user', 'timestamp')
    list_filter = ('action', 'content_type', 'timestamp')
    readonly_fields = ('id', 'content_type', 'object_id', 'action', 'changes', 'user', 'timestamp')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
