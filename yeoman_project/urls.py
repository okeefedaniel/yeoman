from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path

from django.views.generic import RedirectView, TemplateView

from keel.core.demo import demo_login_view
from keel.core.views import SuiteLogoutView, favicon_view, health_check, robots_txt
from keel.core.search_views import search_view
from yeoman.helm_feed import yeoman_helm_feed
from yeoman.helm_inbox import yeoman_helm_feed_inbox
from yeoman.api.intake import invitation_intake
from yeoman.forms import LoginForm

urlpatterns = [
    # Support (shared keel page — linked from 500.html)
    path('support/', TemplateView.as_view(template_name='keel/support.html'), name='support'),
    # User-facing help & manual
    path('help/', TemplateView.as_view(template_name='help.html'), name='help'),
    path('manual/', TemplateView.as_view(template_name='user_manual.html'), name='manual'),
    path('health/', health_check, name='health_check'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('admin/', admin.site.urls),
    # Canonical login lives at /accounts/login/, matching the rest of the
    # suite. The legacy /auth/login/ is preserved as a 301. allauth stays
    # mounted at /auth/ so the registered OIDC redirect_uri
    # (/auth/oidc/keel/login/callback/) keeps working without a Keel DB
    # change. (ISSUE-019)
    path('accounts/login/', LoginView.as_view(
        template_name='account/login.html',
        authentication_form=LoginForm,
    ), name='account_login'),
    path('accounts/logout/', SuiteLogoutView.as_view(), name='account_logout'),
    path(
        'auth/login/',
        RedirectView.as_view(url='/accounts/login/', permanent=True),
    ),
    path('auth/logout/', SuiteLogoutView.as_view()),
    # Demo login (one-click role-based login when DEMO_MODE=True)
    path('demo-login/', demo_login_view, name='demo_login'),
    # Allauth handles everything else (signup, SSO, MFA, password reset).
    # Kept at /auth/ to preserve the OIDC callback URL.
    path('auth/', include('allauth.urls')),
    # Helm executive dashboard feed
    path('api/v1/helm-feed/', yeoman_helm_feed, name='helm-feed'),
    path('api/v1/helm-feed/inbox/', yeoman_helm_feed_inbox, name='helm-feed-inbox'),
    # External intake API (dokeefect.com → Yeoman)
    path('api/v1/intake/invitation/', invitation_intake, name='intake-invitation'),
    path('', include('yeoman.urls')),
    path('search/', search_view, name='search'),
    path('notifications/', include('keel.notifications.urls')),
    path('settings/', include('keel.settings.urls')),
]
