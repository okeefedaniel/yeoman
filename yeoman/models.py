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


class InvitationQuerySet(models.QuerySet):
    """Security-critical scoping helpers.

    Every invitation view MUST resolve records through ``for_user`` (or an
    equivalent agency filter) to prevent IDOR. Invitation UUIDs leak via
    notification emails and calendar links, so relying on the detail URL
    being hard to guess is not sufficient.
    """

    def for_user(self, user):
        if not getattr(user, 'is_authenticated', False):
            return self.none()
        if getattr(user, 'is_superuser', False):
            return self
        agency = getattr(user, 'agency', None) or getattr(user, 'agency_id', None)
        if not agency:
            # No agency binding → only records where the user is directly
            # assigned/delegated/created can be touched.
            return self.filter(
                models.Q(assigned_to=user)
                | models.Q(delegated_to=user)
                | models.Q(created_by=user)
            )
        return self.filter(
            models.Q(agency=agency)
            | models.Q(assigned_to=user)
            | models.Q(delegated_to=user)
            | models.Q(created_by=user)
        )


class InvitationManager(models.Manager.from_queryset(InvitationQuerySet)):
    pass


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
    # event_name / event_date / event_time_start are all optional — many
    # inbound requests arrive with only "I'd like to have the principal
    # speak, date TBD". We fill a derived event_name on save if blank
    # and let staff nail down the date/time during triage.
    event_name = models.CharField(max_length=500, blank=True)
    event_description = models.TextField(blank=True)
    event_date = models.DateField(null=True, blank=True)
    event_time_start = models.TimeField(null=True, blank=True)
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
    # Modality defaults to in_person because that's the most common ask;
    # staff flip it on review if the submitter's request is ambiguous.
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES, default='in_person')

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
        help_text="The claimant — staff member who manages logistics and confirmations.",
    )
    principal = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='principal_invitations',
        help_text="The principal — person attending to speak at the event.",
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
    calendar_sent_to = models.TextField(
        blank=True,
        help_text="Comma-separated emails that received the calendar invite.",
    )
    calendar_sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )

    # === Submitter Status Token ===
    status_token = models.UUIDField(default=uuid.uuid4, editable=False)

    objects = InvitationManager()

    # === Beacon (CRM) sync ===
    BEACON_STATUS_CHOICES = [
        ('', 'Undecided'),
        ('added', 'Added to Beacon'),
        ('declined', 'Skipped'),
    ]
    beacon_status = models.CharField(
        max_length=10, choices=BEACON_STATUS_CHOICES, blank=True, default='',
        help_text="Whether this submitter has been pushed to Beacon.",
    )
    beacon_contact_id = models.CharField(max_length=64, blank=True)
    beacon_decided_at = models.DateTimeField(null=True, blank=True)
    beacon_decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )

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
        if not self.event_date:
            return False
        return self.event_date < timezone.now().date()

    @property
    def needs_date(self):
        """True when the submitter didn't pin down a date/time."""
        return not self.event_date or not self.event_time_start

    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None

    def save(self, **kwargs):
        # Derive a placeholder event_name when the submitter left it
        # blank — staff still need something to scan in the list view.
        if not self.event_name:
            label = dict(self.FORMAT_CHOICES).get(self.event_format, 'Event')
            who = self.submitter_name or self.submitter_organization or 'Unknown'
            self.event_name = f'{label} — {who}'[:500]
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


class PrincipalProfile(models.Model):
    """The principal whose time is being scheduled.

    One per agency. Stores identity info and reference addresses
    used for driving-distance calculations on incoming invitations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.OneToOneField(
        'keel_accounts.Agency', on_delete=models.CASCADE, related_name='principal_profile',
    )
    display_name = models.CharField(max_length=255, help_text="e.g. Commissioner O'Keefe")
    title = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Principal Profile'

    def __str__(self):
        return f"{self.display_name} ({self.agency.abbreviation})"


class ReferenceAddress(models.Model):
    """A named location used for distance calculations.

    Flexible — could be "Home", "Office", "Hartford Capitol", etc.
    Distances from each address are computed when an invitation arrives.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        PrincipalProfile, on_delete=models.CASCADE, related_name='addresses',
    )
    label = models.CharField(max_length=100, help_text="e.g. Home, Office, Capitol")
    address = models.TextField()
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
    )
    is_default = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'label']
        verbose_name = 'Reference Address'
        verbose_name_plural = 'Reference Addresses'

    def __str__(self):
        return f"{self.label}: {self.address[:50]}"


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
