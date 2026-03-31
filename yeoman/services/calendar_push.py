import logging

logger = logging.getLogger(__name__)


class CalendarPushBackend:
    """Abstract base. Subclass for each calendar provider."""

    def push_event(self, invitation) -> str:
        """Create event, return external event ID."""
        raise NotImplementedError

    def cancel_event(self, external_event_id) -> bool:
        raise NotImplementedError

    def update_event(self, external_event_id, invitation) -> bool:
        raise NotImplementedError


class GoogleCalendarBackend(CalendarPushBackend):
    """
    Push via Google Calendar API.
    Stub — full implementation requires OAuth2 credentials.
    """

    def push_event(self, invitation):
        logger.info(
            "[CALENDAR PUSH] Would push to Google Calendar: %s on %s",
            invitation.event_name,
            invitation.event_date,
        )
        return f"google-stub-{invitation.pk}"

    def cancel_event(self, external_event_id):
        logger.info("[CALENDAR PUSH] Would cancel: %s", external_event_id)
        return True

    def update_event(self, external_event_id, invitation):
        logger.info("[CALENDAR PUSH] Would update: %s", external_event_id)
        return True


class ExchangeCalendarBackend(CalendarPushBackend):
    """Push via Microsoft Graph API. Stub — implement when credentials available."""

    def push_event(self, invitation):
        logger.info(
            "[CALENDAR PUSH] Would push to Exchange: %s on %s",
            invitation.event_name,
            invitation.event_date,
        )
        return f"exchange-stub-{invitation.pk}"

    def cancel_event(self, external_event_id):
        logger.info("[CALENDAR PUSH] Would cancel Exchange event: %s", external_event_id)
        return True

    def update_event(self, external_event_id, invitation):
        logger.info("[CALENDAR PUSH] Would update Exchange event: %s", external_event_id)
        return True
