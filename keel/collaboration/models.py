from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from keel.audit.mixins import AuditableMixin


class Thread(AuditableMixin, models.Model):
    """
    A discussion thread attached to any model instance via GenericForeignKey.
    One Thread per target object. Created automatically on first comment.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    target = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='locked_threads',
    )
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"Thread on {self.content_type.model} #{self.object_id}"


class Comment(AuditableMixin, models.Model):
    """
    A single comment in a thread. Supports:
    - Flat threading (parent comment for replies)
    - @mentions (parsed from body, stored in CommentMention)
    - Attachments (via keel.documents)
    - Soft delete (author or admin can remove)
    """
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='collaboration_comments',
    )
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='replies',
    )
    body = models.TextField()
    body_html = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='deleted_comments',
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f"Comment by {self.author} on {self.thread}"


class CommentMention(models.Model):
    """Tracks @mentions in comments. Parsed from body on save."""
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name='mentions',
    )
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='collaboration_mentions',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'mentioned_user')


class ThreadSubscription(models.Model):
    """
    Users subscribed to a thread receive notifications on new comments.
    Auto-created when a user comments, is @mentioned, or manually subscribes.
    """
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name='subscriptions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='thread_subscriptions',
    )
    is_muted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('thread', 'user')
