import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def geocode_invitation(invitation):
    """
    Geocode venue address to lat/lng using Google Geocoding API.
    Called in Invitation.save() when address is present but coordinates are not.
    Fails silently — missing geocodes don't block workflow.
    """
    if not invitation.venue_address or (invitation.latitude and invitation.longitude):
        return

    api_key = getattr(settings, 'GOOGLE_GEOCODING_API_KEY', '')
    if not api_key:
        logger.debug("No GOOGLE_GEOCODING_API_KEY configured, skipping geocode.")
        return

    address_parts = [
        invitation.venue_name,
        invitation.venue_address,
        invitation.venue_city,
        invitation.venue_state,
        invitation.venue_zip,
    ]
    full_address = ', '.join(part for part in address_parts if part)

    try:
        response = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json',
            params={
                'address': full_address,
                'key': api_key,
            },
            timeout=5,
        )
        data = response.json()
        if data['status'] == 'OK' and data['results']:
            loc = data['results'][0]['geometry']['location']
            invitation.latitude = loc['lat']
            invitation.longitude = loc['lng']
    except Exception:
        logger.exception("Geocoding failed for: %s", full_address)
