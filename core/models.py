"""
Yeoman core models — product-specific concrete implementations
of Keel abstract base classes (following Purser pattern).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from keel.core.models import AbstractAuditLog, AbstractNotification
from keel.notifications.models import AbstractNotificationPreference, AbstractNotificationLog
from keel.calendar.models import AbstractCalendarEvent, AbstractCalendarSyncLog


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


class CalendarEvent(AbstractCalendarEvent):
    """Yeoman calendar event — tracks events synced to external calendars."""

    class Meta(AbstractCalendarEvent.Meta):
        verbose_name = _('Calendar Event')
        verbose_name_plural = _('Calendar Events')


class CalendarSyncLog(AbstractCalendarSyncLog):
    """Yeoman calendar sync log."""

    class Meta(AbstractCalendarSyncLog.Meta):
        verbose_name = _('Calendar Sync Log')
        verbose_name_plural = _('Calendar Sync Logs')
