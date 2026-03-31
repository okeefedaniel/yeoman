from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('template_slug', 'recipient', 'is_read', 'channel', 'created_at')
    list_filter = ('template_slug', 'is_read', 'channel')
    readonly_fields = ('id', 'recipient', 'template_slug', 'title', 'body', 'channel', 'created_at')
