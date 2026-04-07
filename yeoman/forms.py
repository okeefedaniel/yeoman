from django import forms
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML

from yeoman.models import Invitation
from keel.accounts.forms import LoginForm  # noqa: F401


# LoginForm is now shared in Keel for suite-wide consistency.

class InvitationStaffForm(forms.ModelForm):
    """Staff form for editing invitation workflow fields."""

    class Meta:
        model = Invitation
        fields = [
            'priority', 'assigned_to', 'event_name', 'event_description',
            'event_date', 'event_time_start', 'event_time_end',
            'event_format', 'modality', 'venue_name', 'venue_address',
            'venue_city', 'venue_state', 'venue_zip',
            'virtual_platform', 'virtual_link',
            'expected_attendees', 'surrogate_ok',
            'press_expected', 'will_be_recorded',
        ]
        widgets = {
            'event_description': forms.Textarea(attrs={'rows': 3}),
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'event_time_start': forms.TimeInput(attrs={'type': 'time'}),
            'event_time_end': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Event Details',
                'event_name',
                Row(
                    Column('event_date', css_class='col-md-4'),
                    Column('event_time_start', css_class='col-md-4'),
                    Column('event_time_end', css_class='col-md-4'),
                ),
                Row(
                    Column('event_format', css_class='col-md-6'),
                    Column('modality', css_class='col-md-6'),
                ),
                'event_description',
            ),
            Fieldset(
                'Location',
                'venue_name',
                'venue_address',
                Row(
                    Column('venue_city', css_class='col-md-6'),
                    Column('venue_state', css_class='col-md-3'),
                    Column('venue_zip', css_class='col-md-3'),
                ),
                Row(
                    Column('virtual_platform', css_class='col-md-6'),
                    Column('virtual_link', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Workflow',
                Row(
                    Column('priority', css_class='col-md-6'),
                    Column('assigned_to', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Logistics',
                Row(
                    Column('expected_attendees', css_class='col-md-3'),
                    Column('surrogate_ok', css_class='col-md-3'),
                    Column('press_expected', css_class='col-md-3'),
                    Column('will_be_recorded', css_class='col-md-3'),
                ),
            ),
            Submit('submit', 'Save Changes', css_class='btn btn-primary'),
        )


class PublicInvitationForm(forms.ModelForm):
    """Public-facing invitation submission form (no login required)."""

    class Meta:
        model = Invitation
        fields = [
            'submitter_first_name', 'submitter_last_name',
            'submitter_email', 'submitter_phone', 'submitter_organization',
            'submitter_title',
            'event_name', 'event_description', 'event_date',
            'event_time_start', 'event_time_end',
            'event_format', 'event_format_other', 'modality',
            'venue_name', 'venue_address', 'venue_city', 'venue_state', 'venue_zip',
            'virtual_platform', 'virtual_link',
            'expected_attendees', 'surrogate_ok',
            'press_expected', 'will_be_recorded',
        ]
        widgets = {
            'event_description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional'}),
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'event_time_start': forms.TimeInput(attrs={'type': 'time'}),
            'event_time_end': forms.TimeInput(attrs={'type': 'time'}),
            'venue_address': forms.TextInput(),
        }

    attachment = forms.FileField(
        required=False,
        help_text='Invite, presentation, agenda, etc. Max 10MB.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make date/time optional for flexible submitters
        self.fields['event_date'].required = False
        self.fields['event_time_start'].required = False
        self.fields['event_name'].widget.attrs['placeholder'] = 'Event Name'
        self.fields['submitter_first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['submitter_last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['submitter_email'].widget.attrs['placeholder'] = 'Email'
        self.fields['submitter_organization'].widget.attrs['placeholder'] = 'Name of Organization'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        self.helper.layout = Layout(
            Fieldset(
                'Your Information',
                Row(
                    Column('submitter_first_name', css_class='col-md-6'),
                    Column('submitter_last_name', css_class='col-md-6'),
                ),
                'submitter_email',
                'submitter_organization',
                Row(
                    Column('submitter_phone', css_class='col-md-6'),
                    Column('submitter_title', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Event Details',
                'event_name',
                HTML('<p class="text-muted small">You can leave date and time blank if you\'re flexible.</p>'),
                Row(
                    Column('event_date', css_class='col-md-4'),
                    Column('event_time_start', css_class='col-md-4'),
                    Column('event_time_end', css_class='col-md-4'),
                ),
                Row(
                    Column('event_format', css_class='col-md-6'),
                    Column('modality', css_class='col-md-6'),
                ),
                'event_format_other',
                'event_description',
            ),
            Fieldset(
                'Location',
                'venue_name',
                'venue_address',
                Row(
                    Column('venue_city', css_class='col-md-6'),
                    Column('venue_state', css_class='col-md-3'),
                    Column('venue_zip', css_class='col-md-3'),
                ),
                Row(
                    Column('virtual_platform', css_class='col-md-6'),
                    Column('virtual_link', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Additional Details',
                Row(
                    Column('expected_attendees', css_class='col-md-6'),
                    Column('surrogate_ok', css_class='col-md-6'),
                ),
                Row(
                    Column('press_expected', css_class='col-md-6'),
                    Column('will_be_recorded', css_class='col-md-6'),
                ),
                'attachment',
            ),
            Submit('submit', 'Submit Invitation', css_class='btn btn-primary btn-lg w-100'),
        )
