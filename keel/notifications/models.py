import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """In-app notification. Stub for keel.notifications."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications',
    )
    template_slug = models.CharField(max_length=100)
    title = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    channel = models.CharField(max_length=20, default='in_app')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'keel_notifications_notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.template_slug} → {self.recipient}"
