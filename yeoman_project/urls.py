from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from yeoman.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    # Custom login/logout views to use our styled templates (before allauth)
    path('auth/login/', LoginView.as_view(
        template_name='account/login.html',
        authentication_form=LoginForm,
    ), name='account_login'),
    path('auth/logout/', LogoutView.as_view(), name='account_logout'),
    # Allauth handles everything else (signup, SSO, MFA, password reset)
    path('auth/', include('allauth.urls')),
    path('', include('yeoman.urls')),
]
