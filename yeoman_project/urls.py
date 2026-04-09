from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path

from keel.core.demo import demo_login_view
from keel.core.views import SuiteLogoutView
from keel.core.search_views import search_view
from yeoman.helm_feed import yeoman_helm_feed
from yeoman.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    # Custom login/logout views to use our styled templates (before allauth)
    path('auth/login/', LoginView.as_view(
        template_name='account/login.html',
        authentication_form=LoginForm,
    ), name='account_login'),
    path('auth/logout/', SuiteLogoutView.as_view(), name='account_logout'),
    # Demo login (one-click role-based login when DEMO_MODE=True)
    path('demo-login/', demo_login_view, name='demo_login'),
    # Allauth handles everything else (signup, SSO, MFA, password reset)
    path('auth/', include('allauth.urls')),
    # Helm executive dashboard feed
    path('api/v1/helm-feed/', yeoman_helm_feed, name='helm-feed'),
    path('', include('yeoman.urls')),
    path('search/', search_view, name='search'),
]
