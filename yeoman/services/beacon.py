"""Optional Beacon (CRM) integration.

Pushes invitation submitters into Beacon's contact intake API on demand.
The "add to Beacon" UI is gated on :func:`is_available` so the button only
appears when this deployment is actually wired up to a Beacon instance.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def is_available():
    """True when this Yeoman deployment can talk to a Beacon instance.

    Both the URL and an API key must be configured. In a single-suite
    deployment these are wired automatically; in standalone mode the
    operator opts in by setting them.
    """
    return bool(
        getattr(settings, 'BEACON_INTAKE_URL', '')
        and getattr(settings, 'BEACON_INTAKE_API_KEY', '')
    )


def push_invitation(invitation):
    """POST the invitation submitter to Beacon's contact intake.

    Returns the new/updated Beacon contact id. Raises on error.
    """
    url = settings.BEACON_INTAKE_URL.rstrip('/')
    payload = {
        'first_name': invitation.submitter_first_name,
        'last_name': invitation.submitter_last_name,
        'email': invitation.submitter_email,
        'phone': invitation.submitter_phone,
        'organization': invitation.submitter_organization,
        'source': 'yeoman',
        'source_label': f'Invitation: {invitation.event_name}'[:255],
        'notes': (
            f'Submitted invitation for "{invitation.event_name}" '
            f'on {invitation.event_date.isoformat()}.'
        ),
    }
    response = requests.post(
        url,
        json=payload,
        headers={'Authorization': f'Bearer {settings.BEACON_INTAKE_API_KEY}'},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    contact_id = data.get('id', '')
    logger.info(
        'Pushed invitation %s submitter to Beacon contact %s',
        invitation.pk, contact_id,
    )
    return contact_id
