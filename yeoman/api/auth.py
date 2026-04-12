"""Bearer-token authentication for external intake endpoints.

Follows the same pattern as keel/feed/views.py — compares the
Authorization header against a per-endpoint API key stored in settings.
CSRF is exempt because callers are external services, not browsers.
"""
import functools
import hmac
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def intake_api_view(settings_key):
    """Decorator factory for intake API endpoints.

    Usage::

        @intake_api_view('YEOMAN_INTAKE_API_KEY')
        def my_view(request):
            ...
            return JsonResponse({...})

    Auth: ``Authorization: Bearer <token>`` matched against the named setting.
    In DEMO_MODE auth is bypassed so the demo instance works without secrets.
    """

    def decorator(view_func):
        @csrf_exempt
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Only allow POST
            if request.method != 'POST':
                return JsonResponse({'error': 'Method not allowed.'}, status=405)

            demo_mode = getattr(settings, 'DEMO_MODE', False)

            if not demo_mode:
                api_key = getattr(settings, settings_key, '') or ''
                if not api_key:
                    return JsonResponse(
                        {'error': f'Intake endpoint not configured ({settings_key} missing).'},
                        status=503,
                    )

                auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                if not auth_header.startswith('Bearer ') or not hmac.compare_digest(
                    auth_header[7:].strip(), api_key
                ):
                    return JsonResponse({'error': 'Invalid API key.'}, status=401)

            try:
                return view_func(request, *args, **kwargs)
            except Exception:
                logger.exception('Error in intake endpoint %s', request.path)
                return JsonResponse({'error': 'Internal server error.'}, status=500)

        return wrapper

    return decorator
