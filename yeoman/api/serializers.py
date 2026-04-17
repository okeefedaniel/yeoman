"""Serializers for the Yeoman intake API."""
from rest_framework import serializers


# Maps dokeefect.com form values to Yeoman model choices
EVENT_TYPE_MAP = {
    'presentation': 'presentation',
    'keynote': 'keynote',
    'moderator': 'panel_moderator',
    'panel participant': 'panel_participant',
    'panel_participant': 'panel_participant',
    'site visit': 'site_visit',
    'site_visit': 'site_visit',
    'roundtable': 'roundtable',
    'ribbon cutting': 'ribbon_cutting',
    'ribbon_cutting': 'ribbon_cutting',
    'meeting': 'meeting',
    'reception': 'reception',
    'conference': 'conference',
    'fireside': 'fireside',
    'tour': 'tour',
    'other': 'other',
}

MODALITY_MAP = {
    'virtual': 'virtual',
    'in person': 'in_person',
    'in_person': 'in_person',
    'hybrid': 'hybrid',
}


class InvitationIntakeSerializer(serializers.Serializer):
    """Validates and normalises data from the dokeefect.com Invite form.

    Required: identity (name + email) and event_type. Everything else —
    date, time, venue, modality, event_name — is optional so submitters
    with "anytime this spring, you pick" requests aren't blocked.
    """

    # Submitter. Accept either split first/last OR a combined "name"
    # which is split on the last whitespace.
    first_name = serializers.CharField(max_length=128, required=False, default='', allow_blank=True)
    last_name = serializers.CharField(max_length=128, required=False, default='', allow_blank=True)
    name = serializers.CharField(max_length=256, required=False, default='', allow_blank=True)
    email = serializers.EmailField()
    organization = serializers.CharField(max_length=255, required=False, default='', allow_blank=True)

    # Event details
    event_name = serializers.CharField(max_length=500, required=False, default='', allow_blank=True)
    event_date = serializers.DateField(required=False, allow_null=True, default=None)
    start_time = serializers.TimeField(required=False, allow_null=True, default=None)
    end_time = serializers.TimeField(required=False, allow_null=True, default=None)

    # Type / format. event_type is our one required triage field — we
    # need to know whether it's a keynote, a panel, a ribbon-cutting,
    # etc. before routing. "other" is the escape hatch.
    event_type = serializers.CharField(max_length=50)
    event_format = serializers.CharField(max_length=50, required=False, default='in_person', allow_blank=True)

    # Location
    location = serializers.CharField(max_length=1000, required=False, default='', allow_blank=True)

    # Logistics
    attendees = serializers.IntegerField(required=False, allow_null=True, default=None)
    proxy = serializers.CharField(max_length=10, required=False, default='yes', allow_blank=True)
    press = serializers.CharField(max_length=10, required=False, default='unknown', allow_blank=True)
    event_recorded = serializers.CharField(max_length=10, required=False, default='unknown', allow_blank=True)

    # Notes
    notes = serializers.CharField(required=False, default='', allow_blank=True)

    def validate_event_type(self, value):
        normalised = EVENT_TYPE_MAP.get(value.lower().strip())
        if not normalised:
            raise serializers.ValidationError(
                f'Unknown event_type "{value}". '
                f'Valid values: {", ".join(sorted(EVENT_TYPE_MAP.keys()))}'
            )
        return normalised

    def validate_event_format(self, value):
        if not value or not value.strip():
            return 'in_person'
        normalised = MODALITY_MAP.get(value.lower().strip())
        if not normalised:
            raise serializers.ValidationError(
                f'Unknown event_format "{value}". '
                f'Valid values: {", ".join(sorted(MODALITY_MAP.keys()))}'
            )
        return normalised

    def validate_proxy(self, value):
        return value.lower().strip() in ('yes', 'true', '1')

    def validate_press(self, value):
        v = value.lower().strip()
        if v in ('yes', 'true', '1'):
            return 'yes'
        if v in ('no', 'false', '0'):
            return 'no'
        return 'unknown'

    def validate_event_recorded(self, value):
        v = value.lower().strip()
        if v in ('yes', 'true', '1'):
            return 'yes'
        if v in ('no', 'false', '0'):
            return 'no'
        return 'unknown'

    def validate(self, data):
        """Merge the convenience `name` field into first_name/last_name.

        If the caller sent a combined "name", split on the last space so
        "Jane Q Public" → ("Jane Q", "Public"). Then require at least
        first_name (last_name may be blank for one-word names).
        """
        combined = (data.pop('name', '') or '').strip()
        if combined and not data.get('first_name') and not data.get('last_name'):
            parts = combined.rsplit(' ', 1)
            if len(parts) == 2:
                data['first_name'], data['last_name'] = parts[0], parts[1]
            else:
                data['first_name'], data['last_name'] = combined, ''

        if not data.get('first_name'):
            raise serializers.ValidationError({
                'name': 'A submitter name is required (send `name` or '
                        '`first_name`+`last_name`).',
            })
        return data
