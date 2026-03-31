import uuid

from django.conf import settings
from django.db import models

from keel.audit.mixins import AuditableMixin
from keel.orgs.models import Organization
from keel.workflow.mixins import WorkflowMixin


class InvitationTag(models.Model):
    """Flexible tagging for invitations. Examples: 'legislative', 'economic-dev', 'education'."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='invitation_tags',
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    color = models.CharField(max_length=7, default='#6c757d')

    class Meta:
        unique_together = ('org', 'slug')
        ordering = ['name']

    def __str__(self):
        return self.name


class Invitation(AuditableMixin, WorkflowMixin, models.Model):
    """
    The core record. Represents a request for the principal's time.
    Created either via the public intake form or manually by staff.
    """
    WORKFLOW_NAME = 'yeoman_invitation'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='invitations',
    )

    # === Submitter Info ===
    submitter_name = models.CharField(max_length=255)
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
        ('roundtable', 'Roundtable'),
        ('keynote', 'Keynote'),
        ('panel', 'Panel'),
        ('fireside', 'Fireside Chat'),
        ('ribbon_cutting', 'Ribbon Cutting'),
        ('tour', 'Tour / Site Visit'),
        ('meeting', 'Meeting'),
        ('reception', 'Reception'),
        ('conference', 'Conference'),
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

    # === Outcome ===
    decline_reason = models.TextField(blank=True)
    calendar_event_id = models.CharField(
        max_length=500, blank=True,
        help_text="External calendar event ID after push (Exchange/Google).",
    )
    calendar_pushed_at = models.DateTimeField(null=True, blank=True)

    # === Submitter Status Token ===
    status_token = models.UUIDField(default=uuid.uuid4, editable=False)

    # === Meta ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='created_invitations',
    )

    class Meta:
        ordering = ['-event_date', '-created_at']
        indexes = [
            models.Index(fields=['org', 'status']),
            models.Index(fields=['event_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['delegated_to']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.event_name} ({self.event_date})"

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


class InvitationAttachment(AuditableMixin, models.Model):
    """File attachments on an invitation. Uses keel.documents for storage."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(
        Invitation, on_delete=models.CASCADE, related_name='attachments',
    )
    document = models.ForeignKey(
        'keel_documents.Document', on_delete=models.CASCADE,
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
        return f"{self.document.original_filename} on {self.invitation}"


class DelegationLog(AuditableMixin, models.Model):
    """Tracks the full delegation history of an invitation."""
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
        return f"{self.delegated_by} → {self.delegated_to} on {self.invitation}"
