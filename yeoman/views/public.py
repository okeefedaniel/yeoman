import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView, DetailView

from keel.notifications.dispatch import notify

from keel.accounts.models import Agency
from yeoman.forms import PublicInvitationForm
from yeoman.models import Invitation, InvitationAttachment
from yeoman.workflow import STATUS_DISPLAY


logger = logging.getLogger(__name__)


def _client_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    return ip.split(',')[0].strip() if ip else ''


def _is_spam(request):
    """Return True if submission looks like spam.

    Checks honeypot `website` field and Cloudflare Turnstile token.
    Fails open on Turnstile network errors. Returns False when no secret
    is configured (dev/local).
    """
    ip = _client_ip(request)

    if request.POST.get('website', '').strip():
        logger.warning(f"Yeoman spam blocked (honeypot) from {ip}")
        return True

    secret = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    if not secret:
        return False

    token = request.POST.get('cf-turnstile-response', '')
    if not token:
        logger.warning(f"Yeoman spam blocked (missing Turnstile token) from {ip}")
        return True

    try:
        import requests
        resp = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={'secret': secret, 'response': token, 'remoteip': ip},
            timeout=5,
        )
        if not resp.json().get('success', False):
            logger.warning(f"Yeoman spam blocked (Turnstile failed) from {ip}")
            return True
    except Exception as e:
        logger.error(f"Turnstile verify error (failing open): {e}")
        return False

    return False


class PublicInviteView(FormView):
    template_name = 'yeoman/public_invite.html'
    form_class = PublicInvitationForm

    def dispatch(self, request, *args, **kwargs):
        # Simple IP-based rate limiting
        ip = _client_ip(request)
        cache_key = f'yeoman_invite_rate_{ip}'
        count = cache.get(cache_key, 0)
        limit = getattr(settings, 'YEOMAN_PUBLIC_FORM_RATE_LIMIT', '10/h')
        max_count = int(limit.split('/')[0]) if '/' in limit else 10
        if count >= max_count:
            messages.error(request, 'Too many submissions. Please try again later.')
            return self.render_to_response(self.get_context_data())

        # Spam check on POST (honeypot + Turnstile). Silently redirect to the
        # success page so bots don't retry.
        if request.method == 'POST' and _is_spam(request):
            return HttpResponseRedirect(reverse('yeoman:invite_success'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['turnstile_site_key'] = getattr(settings, 'TURNSTILE_SITE_KEY', '')
        return ctx

    def form_valid(self, form):
        invitation = form.save(commit=False)
        # Set default agency (first active, or create DECD)
        agency = Agency.objects.filter(is_active=True).first()
        if not agency:
            agency = Agency.objects.create(name='Default Agency', abbreviation='DEFAULT')
        invitation.agency = agency
        invitation.status = 'received'
        invitation.save()

        # Handle file attachment (validated by Keel FileSecurityValidator)
        attachment = self.request.FILES.get('attachment')
        if attachment:
            from keel.security.scanning import FileSecurityValidator
            validator = FileSecurityValidator()
            try:
                validator(attachment)
                InvitationAttachment.objects.create(
                    invitation=invitation,
                    file=attachment,
                    original_filename=attachment.name,
                    content_type=attachment.content_type or '',
                    size_bytes=attachment.size,
                    uploaded_by_staff=False,
                )
            except Exception:
                pass  # Skip invalid files silently on public form

        # Rate limit tracking
        ip = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR', ''))
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        cache_key = f'yeoman_invite_rate_{ip}'
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, 3600)  # 1 hour window

        # Notify admins/schedulers of the new invitation (role-based resolution)
        notify(
            event='invitation_received',
            context={'invitation': invitation},
            title=str(invitation.event_name),
            message=f'New invitation from {invitation.submitter_name} ({invitation.submitter_organization}).',
            link=f'/invitations/{invitation.pk}/',
        )

        self.status_token = invitation.status_token
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('yeoman:invite_success') + f'?token={self.status_token}'


class InvitationStatusView(DetailView):
    template_name = 'yeoman/invite_status.html'
    context_object_name = 'invitation'

    def get_object(self, queryset=None):
        return get_object_or_404(Invitation, status_token=self.kwargs['token'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['STATUS_DISPLAY'] = STATUS_DISPLAY
        return ctx
