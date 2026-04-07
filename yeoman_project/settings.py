"""
Yeoman - Scheduling & Invitation Workflow
Django settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-key-change-in-production'
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set in production')

DEMO_MODE = os.environ.get('DEMO_MODE', 'False').lower() in ('true', '1', 'yes')
DEMO_ROLES = ['yeoman_admin', 'yeoman_scheduler', 'yeoman_viewer', 'yeoman_delegate']

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

RAILWAY_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
if RAILWAY_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_DOMAIN)
    ALLOWED_HOSTS.append('.railway.app')

# Custom domain
ALLOWED_HOSTS.append('.docklabs.ai')

CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
if RAILWAY_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RAILWAY_DOMAIN}')
CSRF_TRUSTED_ORIGINS.append('https://yeoman.docklabs.ai')
CSRF_TRUSTED_ORIGINS = [o for o in CSRF_TRUSTED_ORIGINS if o]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    # Keel (DockLabs shared platform)
    'keel.accounts',
    'keel.core',
    'keel.security',
    'keel.notifications',
    'keel.requests',
    'keel.calendar',
    # Third party
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    # Allauth (SSO / MFA)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.microsoft',
    'allauth.socialaccount.providers.openid_connect',  # Phase 2b: Keel as IdP
    'allauth.mfa',
    # Project apps
    'core.apps.CoreConfig',
    'yeoman.apps.YeomanConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'keel.security.middleware.SecurityHeadersMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'keel.accounts.middleware.ProductAccessMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'keel.core.middleware.AuditMiddleware',
    'keel.security.middleware.FailedLoginMonitor',
]

ROOT_URLCONF = 'yeoman_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'keel.core.context_processors.site_context',
                'keel.core.context_processors.fleet_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'yeoman_project.wsgi.application'

# Database
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = 'keel_accounts.KeelUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Login/Logout
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Email — Resend HTTP API for transactional emails (Railway blocks outbound SMTP)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'keel.notifications.backends.resend_backend.ResendEmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'DockLabs <info@docklabs.ai>')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'core': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'yeoman': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# Security
SESSION_COOKIE_AGE = 3600
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
CSRF_COOKIE_SAMESITE = 'Lax'

# Suite mode: shared session cookie across *.docklabs.ai
KEEL_SUITE_DOMAIN = os.environ.get('KEEL_SUITE_DOMAIN')
if KEEL_SUITE_DOMAIN:
    SESSION_COOKIE_DOMAIN = KEEL_SUITE_DOMAIN
    SESSION_COOKIE_NAME = 'docklabs_sessionid'
    CSRF_COOKIE_DOMAIN = KEEL_SUITE_DOMAIN
    CSRF_COOKIE_NAME = 'docklabs_csrftoken'

if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Railway handles SSL termination
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Allauth
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_ADAPTER = 'keel.core.sso.KeelAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'keel.core.sso.KeelSocialAccountAdapter'

_MSFT_TENANT = os.environ.get('MICROSOFT_TENANT_ID', 'common')
SOCIALACCOUNT_PROVIDERS = {
    'microsoft': {
        'APP': {
            'client_id': os.environ.get('MICROSOFT_CLIENT_ID', ''),
            'secret': os.environ.get('MICROSOFT_CLIENT_SECRET', ''),
        },
        'SCOPE': ['openid', 'email', 'profile', 'User.Read'],
        'AUTH_PARAMS': {'prompt': 'select_account'},
        'TENANT': _MSFT_TENANT,
    },
}

# ---------------------------------------------------------------------------
# Keel OIDC (Phase 2b) — Keel is the identity provider for the DockLabs suite
# ---------------------------------------------------------------------------
# When KEEL_OIDC_CLIENT_ID is set, this product federates authentication to
# Keel via standard OAuth2/OIDC. When unset, the product falls back to local
# Django auth (+ optional direct Microsoft SSO), so standalone deployments
# continue to work without any Keel dependency.
KEEL_OIDC_CLIENT_ID = os.environ.get('KEEL_OIDC_CLIENT_ID', '')
KEEL_OIDC_CLIENT_SECRET = os.environ.get('KEEL_OIDC_CLIENT_SECRET', '')
KEEL_OIDC_ISSUER = os.environ.get('KEEL_OIDC_ISSUER', 'https://keel.docklabs.ai')

if KEEL_OIDC_CLIENT_ID:
    SOCIALACCOUNT_PROVIDERS['openid_connect'] = {
        'APPS': [
            {
                'provider_id': 'keel',
                'name': 'Sign in with DockLabs',
                'client_id': KEEL_OIDC_CLIENT_ID,
                'secret': KEEL_OIDC_CLIENT_SECRET,
                'settings': {
                    'server_url': f'{KEEL_OIDC_ISSUER}/oauth/.well-known/openid-configuration',
                    'token_auth_method': 'client_secret_post',
                },
            },
        ],
    }

MFA_ADAPTER = 'allauth.mfa.adapter.DefaultMFAAdapter'
MFA_SUPPORTED_TYPES = ['totp', 'webauthn', 'recovery_codes']
MFA_TOTP_ISSUER = 'Yeoman'
MFA_PASSKEY_LOGIN_ENABLED = True

# Keel
KEEL_GATE_ACCESS = True
KEEL_PRODUCT_CODE = 'yeoman'
KEEL_FLEET_PRODUCTS = [
    {'name': 'Helm', 'label': 'Helm', 'code': 'helm', 'url': '/'},
    {'name': 'Beacon', 'label': 'Beacon', 'code': 'beacon', 'url': '/'},
    {'name': 'Harbor', 'label': 'Harbor', 'code': 'harbor', 'url': '/'},
    {'name': 'Bounty', 'label': 'Bounty', 'code': 'bounty', 'url': '/'},
    {'name': 'Lookout', 'label': 'Lookout', 'code': 'lookout', 'url': '/'},
]
KEEL_PRODUCT_NAME = 'Yeoman'
KEEL_PRODUCT_ICON = 'bi-calendar2-week'
KEEL_PRODUCT_SUBTITLE = 'Event Scheduling & Invitation Workflow'
KEEL_API_URL = os.environ.get('KEEL_API_URL', 'https://keel.docklabs.ai')
KEEL_API_KEY = os.environ.get('KEEL_API_KEY', '')
KEEL_AUDIT_LOG_MODEL = 'yeoman_core.AuditLog'
KEEL_NOTIFICATION_MODEL = 'yeoman_core.Notification'
KEEL_NOTIFICATION_PREFERENCE_MODEL = 'yeoman_core.NotificationPreference'
KEEL_NOTIFICATION_LOG_MODEL = 'yeoman_core.NotificationLog'
KEEL_CSP_POLICY = {}
KEEL_FILE_SCANNING_ENABLED = not DEBUG
KEEL_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
KEEL_ALLOWED_UPLOAD_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.csv', '.txt', '.png', '.jpg', '.jpeg', '.gif',
]

# Calendar sync (keel.calendar)
KEEL_CALENDAR_PROVIDER = os.environ.get('KEEL_CALENDAR_PROVIDER', None)  # 'google' or 'microsoft'
KEEL_CALENDAR_EVENT_MODEL = 'yeoman_core.CalendarEvent'
KEEL_CALENDAR_SYNC_LOG_MODEL = 'yeoman_core.CalendarSyncLog'

# Yeoman-specific
GOOGLE_GEOCODING_API_KEY = os.environ.get('GOOGLE_GEOCODING_API_KEY', '')
MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN', '')

# Site
SITE_NAME = 'Yeoman'
