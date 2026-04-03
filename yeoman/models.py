import uuid

from django.conf import settings
from django.db import models

from keel.core.models import KeelBaseModel, AbstractStatusHistory, AbstractInternalNote, WorkflowModelMixin
from keel.security.scanning import FileSecurityValidator


class InvitationTag(models.Model):
    """Flexible tagging for invitations. Examples: 'legislative', 'economic-dev', 'education'."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey(
        'keel_accounts.Agency', on_delete=models.CASCADE, related_name='invitation_tags',
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    color = models.CharField(max_length=7, default='#6c757d')

    class Meta:
        unique_together = ('agency', 'slug')
        ordering = ['name']

    def __str__(self):
        return self.name


class Invitation(WorkflowModelMixin, KeelBaseModel):
    """
    The core record. Represents a request for the principal's time.
    Created either via the public intake form or manually by staff.
    """
    from yeoman.workflow import INVITATION_WORKFLOW
    WORKFLOW = INVITATION_WORKFLOW

    agency = models.ForeignKey(
        'keel_accounts.Agency', on_delete=models.CASCADE, related_name='invitations',
    )

    # === Status (workflow) ===
    status = models.CharField(max_length=50, default='received', db_index=True)

    # === Submitter Info ===
    submitter_first_name = models.CharField(max_length=128)
    submitter_last_name = models.CharField(max_length=128)
    submitter_email = models.EmailField()
    submitter_phone = models.CharField(max_length=50, blank=True)
    submitter_organization = models.CharField(max_length=255, blank=True)
    submitter_title = models.CharField(max_length=255, blank=True)

    # === Event Details ===
    event_name = models.CharField(max_length=500)
    event_description = models.TextField(blank=True)
    event_date = models.DateField()
    event_time_start = models.TimeField()
    event_time_end = models.TimeField(null=True, blank=True)
    event_timezone = models.CharField(max_length=50, default='America/New_York')

    FORMAT_CHOICES = [
        ('presentation', 'Presentation'),
        ('keynote', 'Keynote'),
        ('panel_moderator', 'Panel Moderator'),
        ('panel_participant', 'Panel Participant'),
        ('site_visit', 'Site Visit'),
        ('roundtable', 'Roundtable'),
        ('ribbon_cutting', 'Ribbon Cutting'),
        ('meeting', 'Meeting'),
        ('reception', 'Reception'),
        ('conference', 'Conference'),
        ('fireside', 'Fireside Chat'),
        ('tour', 'Tour'),
        ('other', 'Other'),
    ]
    event_format = models.CharField(max_length=50, choices=FORMAT_CHOICES)
    event_format_other = models.CharField(max_length=255, blank=True)

    MODALITY_CHOICES = [
        ('in_person', 'In Person'),
        ('virtual', 'Virtual'),
        ('hybrid', 'Hybrid'),
    ]
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES)

    # === Location (for in-person / hybrid) ===
    venue_name = models.CharField(max_length=500, blank=True)
    venue_address = models.TextField(blank=True)
    venue_city = models.CharField(max_length=255, blank=True)
    venue_state = models.CharField(max_length=2, default='CT')
    venue_zip = models.CharField(max_length=10, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
    )

    # === Virtual Details ===
    virtual_platform = models.CharField(max_length=255, blank=True)
    virtual_link = models.URLField(blank=True)

    # === Assignment & Delegation ===
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_invitations',
        help_text="The staff member currently responsible for this invitation.",
    )
    delegated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='delegated_invitations',
        help_text="If delegated, the person who will attend on behalf of the principal.",
    )
    delegated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='delegations_made',
    )
    delegated_at = models.DateTimeField(null=True, blank=True)
    delegation_notes = models.TextField(blank=True)

    # === Priority & Tags ===
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    tags = models.ManyToManyField(InvitationTag, blank=True)

    # === Event Logistics ===
    expected_attendees = models.PositiveIntegerField(null=True, blank=True)
    surrogate_ok = models.BooleanField(
        default=True,
        help_text="Submitter is interested in a surrogate if principal has a conflict.",
    )

    YES_NO_UNKNOWN = [
        ('unknown', 'Unknown'),
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    press_expected = models.CharField(
        max_length=10, choices=YES_NO_UNKNOWN, default='unknown',
    )
    will_be_recorded = models.CharField(
        max_length=10, choices=YES_NO_UNKNOWN, default='unknown',
    )

    # === Outcome ===
    decline_reason = models.TextField(blank=True)
    calendar_event_id = models.CharField(
        max_length=500, blank=True,
        help_text="External calendar event ID after push (Exchange/Google).",
    )
    calendar_pushed_at = models.DateTimeField(null=True, blank=True)

    # === Submitter Status Token ===
    status_token = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        ordering = ['-event_date', '-created_at']
        indexes = [
            models.Index(fields=['agency', 'status']),
            models.Index(fields=['event_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['delegated_to']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.event_name} ({self.event_date})"

    @property
    def submitter_name(self):
        return f"{self.submitter_first_name} {self.submitter_last_name}".strip()

    @property
    def is_past(self):
        from django.utils import timezone
        return self.event_date < timezone.now().date()

    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None

    def save(self, **kwargs):
        # Geocode on save if address present but no coordinates
        if self.venue_address and not (self.latitude and self.longitude):
            from yeoman.services.geocoding import geocode_invitation
            geocode_invitation(self)
        super().save(**kwargs)


class InvitationAttachment(models.Model):
    """File attachments on an invitation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(
        Invitation, on_delete=models.CASCADE, related_name='attachments',
    )
    file = models.FileField(
        upload_to='invitation_attachments/%Y/%m/',
        validators=[FileSecurityValidator()],
    )
    original_filename = models.CharField(max_length=500)
    content_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    uploaded_by_staff = models.BooleanField(
        default=False,
        help_text="True if uploaded by internal staff, False if from submitter.",
    )
    label = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.original_filename} on {self.invitation}"


class InvitationStatusHistory(AbstractStatusHistory):
    """Immutable audit trail of workflow transitions for an invitation."""
    invitation = models.ForeignKey(
        Invitation, on_delete=models.CASCADE, related_name='status_history',
    )

    class Meta(AbstractStatusHistory.Meta):
        verbose_name_plural = 'invitation status histories'


class InvitationNote(AbstractInternalNote):
    """Internal staff note/comment on an invitation."""
    invitation = models.ForeignKey(
        Invitation, on_delete=models.CASCADE, related_name='notes',
    )


class DelegationLog(models.Model):
    """Tracks the full delegation history of an invitation. Immutable."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(
        Invitation, on_delete=models.CASCADE, related_name='delegation_history',
    )
    delegated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='delegation_log_by',
    )
    delegated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='delegation_log_to',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.delegated_by} -> {self.delegated_to} on {self.invitation}"
