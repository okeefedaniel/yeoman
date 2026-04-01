from django.contrib import admin

from .models import DelegationLog, Invitation, InvitationAttachment, InvitationTag


class InvitationAttachmentInline(admin.TabularInline):
    model = InvitationAttachment
    extra = 0
    readonly_fields = ('original_filename', 'uploaded_by_staff', 'created_at')


class DelegationLogInline(admin.TabularInline):
    model = DelegationLog
    extra = 0
    readonly_fields = ('delegated_by', 'delegated_to', 'notes', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        'event_name', 'event_date', 'event_format', 'status',
        'priority', 'submitter_name', 'assigned_to', 'created_at',
    )
    list_filter = ('status', 'event_format', 'modality', 'priority', 'agency')
    search_fields = (
        'event_name', 'submitter_name', 'submitter_email',
        'submitter_organization', 'venue_name',
    )
    readonly_fields = ('id', 'status_token', 'created_at', 'updated_at')
    list_editable = ('priority', 'status')
    date_hierarchy = 'event_date'
    raw_id_fields = ('assigned_to', 'delegated_to', 'delegated_by', 'created_by')
    inlines = [InvitationAttachmentInline, DelegationLogInline]

    fieldsets = (
        ('Event', {
            'fields': (
                'id', 'agency', 'event_name', 'event_description',
                'event_date', 'event_time_start', 'event_time_end',
                'event_timezone', 'event_format', 'event_format_other',
                'modality',
            ),
        }),
        ('Submitter', {
            'fields': (
                'submitter_name', 'submitter_email', 'submitter_phone',
                'submitter_organization', 'submitter_title',
            ),
        }),
        ('Location', {
            'fields': (
                'venue_name', 'venue_address', 'venue_city',
                'venue_state', 'venue_zip', 'latitude', 'longitude',
            ),
            'classes': ('collapse',),
        }),
        ('Virtual', {
            'fields': ('virtual_platform', 'virtual_link'),
            'classes': ('collapse',),
        }),
        ('Workflow', {
            'fields': (
                'status', 'priority', 'assigned_to',
                'delegated_to', 'delegated_by', 'delegated_at',
                'delegation_notes', 'decline_reason',
            ),
        }),
        ('Calendar', {
            'fields': ('calendar_event_id', 'calendar_pushed_at'),
            'classes': ('collapse',),
        }),
        ('Meta', {
            'fields': (
                'tags', 'status_token', 'created_by',
                'created_at', 'updated_at',
            ),
        }),
    )


@admin.register(InvitationTag)
class InvitationTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'agency', 'color')
    list_filter = ('agency',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(InvitationAttachment)
class InvitationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'invitation', 'uploaded_by_staff', 'created_at')
    list_filter = ('uploaded_by_staff',)


@admin.register(DelegationLog)
class DelegationLogAdmin(admin.ModelAdmin):
    list_display = ('invitation', 'delegated_by', 'delegated_to', 'created_at')
    readonly_fields = ('id', 'invitation', 'delegated_by', 'delegated_to', 'notes', 'created_at')

    def has_add_permission(self, request):
        return False
