"""
Yeoman core models — product-specific concrete implementations
of Keel abstract base classes (following Bounty pattern).
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from keel.core.models import AbstractAuditLog, AbstractNotification
from keel.notifications.models import AbstractNotificationPreference, AbstractNotificationLog


class User(AbstractUser):
    """Custom user model for the Yeoman platform."""

    class Role(models.TextChoices):
        ADMIN = 'yeoman_admin', _('Administrator')
        SCHEDULER = 'yeoman_scheduler', _('Scheduler')
        VIEWER = 'yeoman_viewer', _('Viewer')
        DELEGATE = 'yeoman_delegate', _('Delegate')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )
    title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    organization_name = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        full = self.get_full_name()
        return full if full else self.username

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_scheduler(self):
        return self.role in {self.Role.ADMIN, self.Role.SCHEDULER}

    def get_roles(self, org=None):
        """Return list of role names for workflow compatibility."""
        return [self.role]


class Agency(models.Model):
    """Organization / agency stub for Yeoman multi-tenancy."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['abbreviation']
        verbose_name = _('Agency')
        verbose_name_plural = _('Agencies')

    def __str__(self):
        return f"{self.abbreviation} - {self.name}"


class AuditLog(AbstractAuditLog):
    """Yeoman audit log."""

    class Meta(AbstractAuditLog.Meta):
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')


class Notification(AbstractNotification):
    """Yeoman in-app notification."""

    class Meta(AbstractNotification.Meta):
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')


class NotificationPreference(AbstractNotificationPreference):
    """Per-user notification channel preferences."""

    class Meta(AbstractNotificationPreference.Meta):
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')


class NotificationLog(AbstractNotificationLog):
    """Notification delivery log."""

    class Meta(AbstractNotificationLog.Meta):
        verbose_name = _('Notification Log')
        verbose_name_plural = _('Notification Logs')
