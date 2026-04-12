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
    """Validates and normalises data from the dokeefect.com Invite form."""

    # Submitter
    first_name = serializers.CharField(max_length=128)
    last_name = serializers.CharField(max_length=128)
    email = serializers.EmailField()
    organization = serializers.CharField(max_length=255, required=False, default='')

    # Event details
    event_name = serializers.CharField(max_length=500, required=False, default='')
    event_date = serializers.DateField(required=False, allow_null=True, default=None)
    start_time = serializers.TimeField(required=False, allow_null=True, default=None)
    end_time = serializers.TimeField(required=False, allow_null=True, default=None)

    # Type / format
    event_type = serializers.CharField(max_length=50)
    event_format = serializers.CharField(max_length=50, required=False, default='in_person')

    # Location
    location = serializers.CharField(max_length=1000, required=False, default='')

    # Logistics
    attendees = serializers.IntegerField(required=False, allow_null=True, default=None)
    proxy = serializers.CharField(max_length=10, required=False, default='yes')
    press = serializers.CharField(max_length=10, required=False, default='unknown')
    event_recorded = serializers.CharField(max_length=10, required=False, default='unknown')

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
