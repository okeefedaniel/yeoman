import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='dev-insecure-key-change-in-production')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Keel modules (stubs for now — swap for real keel when available)
    'keel.auth',
    'keel.orgs',
    'keel.audit',
    'keel.workflow',
    'keel.notifications',
    'keel.documents',
    'keel.collaboration',
    # Yeoman
    'yeoman',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'yeoman_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'yeoman_project.wsgi.application'

# Database
db_url = env('DATABASE_URL', default='')
if db_url:
    DATABASES = {
        'default': env.db(),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'keel_auth.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='yeoman@docklabs.ai')

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Documents (keel.documents)
DOCUMENTS_STORAGE_BACKEND = env('DOCUMENTS_STORAGE_BACKEND', default='local')
DOCUMENTS_MAX_SIZE_MB = env.int('DOCUMENTS_MAX_SIZE_MB', default=10)
CLAMAV_ENABLED = env.bool('CLAMAV_ENABLED', default=False)

# Geocoding
GOOGLE_GEOCODING_API_KEY = env('GOOGLE_GEOCODING_API_KEY', default='')

# Calendar Push
YEOMAN_CALENDAR_BACKEND = 'yeoman.services.calendar_push.GoogleCalendarBackend'
GOOGLE_CALENDAR_CREDENTIALS_JSON = env('GOOGLE_CALENDAR_CREDENTIALS_JSON', default='')
GOOGLE_CALENDAR_ID = env('GOOGLE_CALENDAR_ID', default='primary')

# Rate limiting
YEOMAN_PUBLIC_FORM_RATE_LIMIT = env('YEOMAN_PUBLIC_FORM_RATE_LIMIT', default='10/h')

# Login
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
