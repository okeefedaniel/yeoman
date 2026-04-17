from django.urls import path
from django.views.generic import RedirectView, TemplateView

from keel.core.views import LandingView

from yeoman.views import (
    DashboardView,
    InvitationListView,
    InvitationDetailView,
    InvitationUpdateView,
    invitation_transition,
    invitation_claim,
    invitation_unclaim,
    invitation_add_note,
    invitation_delegate,
    invitation_beacon_toggle,
    invitation_send_email,
    PublicInviteView,
    InvitationStatusView,
    CalendarView,
    calendar_events_json,
    MapView,
    map_markers_json,
    ReportsDashboardView,
    InvitationExportView,
    PrincipalSettingsView,
)
from yeoman.views.ical import invitation_ical

app_name = 'yeoman'

urlpatterns = [
    # Public landing page (root) — redirects authenticated users to dashboard
    path('', LandingView.as_view(
        template_name='yeoman/landing.html',
        authenticated_redirect='yeoman:dashboard',
        stats=[
            {'value': 'Calendar', 'label': 'Sync'},
            {'value': 'iCal', 'label': 'Export'},
            {'value': 'Multi-event', 'label': 'Workflows'},
            {'value': 'Public', 'label': 'Intake'},
        ],
        features=[
            {'icon': 'bi-calendar2-week', 'title': 'Event Scheduling',
             'description': 'Manage public hearings, agency events, and stakeholder meetings with full calendar integration.',
             'color': 'blue'},
            {'icon': 'bi-people', 'title': 'Invitation Workflow',
             'description': 'Track invitations from intake to completion with status transitions, delegation, and notes.',
             'color': 'teal'},
            {'icon': 'bi-geo-alt', 'title': 'Map View',
             'description': 'Visualize events geographically with location markers and clustering for regional planning.',
             'color': 'yellow'},
        ],
        steps=[
            {'title': 'Receive Invitation', 'description': 'Public submits an invitation via the intake form.'},
            {'title': 'Triage', 'description': 'Staff claim, delegate, or transition invitations through the workflow.'},
            {'title': 'Schedule', 'description': 'Confirmed invitations sync to calendars with iCal export.'},
            {'title': 'Report', 'description': 'Run reports on event activity, response times, and outcomes.'},
        ],
    ), name='landing'),

    # Staff dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Invitations CRUD
    path('invitations/', InvitationListView.as_view(), name='invitation_list'),
    path('invitations/<uuid:pk>/', InvitationDetailView.as_view(), name='invitation_detail'),
    path('invitations/<uuid:pk>/edit/', InvitationUpdateView.as_view(), name='invitation_update'),
    path('invitations/<uuid:pk>/transition/', invitation_transition, name='invitation_transition'),
    path('invitations/<uuid:pk>/claim/', invitation_claim, name='invitation_claim'),
    path('invitations/<uuid:pk>/unclaim/', invitation_unclaim, name='invitation_unclaim'),
    path('invitations/<uuid:pk>/note/', invitation_add_note, name='invitation_add_note'),
    path('invitations/<uuid:pk>/delegate/', invitation_delegate, name='invitation_delegate'),
    path('invitations/<uuid:pk>/beacon/', invitation_beacon_toggle, name='invitation_beacon_toggle'),
    path('invitations/<uuid:pk>/email/', invitation_send_email, name='invitation_send_email'),
    path('invitations/<uuid:pk>/ical/', invitation_ical, name='invitation_ical'),

    # Calendar
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('calendar/events.json', calendar_events_json, name='calendar_events_json'),

    # Map
    path('map/', MapView.as_view(), name='map'),
    path('map/markers.json', map_markers_json, name='map_markers_json'),

    # Public intake
    path('invite/', PublicInviteView.as_view(), name='public_invite'),
    path('invite/success/', TemplateView.as_view(template_name='yeoman/invite_success.html'), name='invite_success'),
    path('invite/status/<uuid:token>/', InvitationStatusView.as_view(), name='invite_status'),

    # Reports
    path('reports/', ReportsDashboardView.as_view(), name='reports'),
    path('reports/export/', InvitationExportView.as_view(), name='reports_export'),

    # Settings
    path('settings/principal/', PrincipalSettingsView.as_view(), name='principal_settings'),
]
