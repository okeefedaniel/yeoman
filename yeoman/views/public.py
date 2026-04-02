from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView, DetailView

from keel.notifications.dispatch import notify

from keel.accounts.models import Agency
from yeoman.forms import PublicInvitationForm
from yeoman.models import Invitation, InvitationAttachment
from yeoman.workflow import STATUS_DISPLAY


class PublicInviteView(FormView):
    template_name = 'yeoman/public_invite.html'
    form_class = PublicInvitationForm

    def dispatch(self, request, *args, **kwargs):
        # Simple IP-based rate limiting
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        cache_key = f'yeoman_invite_rate_{ip}'
        count = cache.get(cache_key, 0)
        limit = getattr(settings, 'YEOMAN_PUBLIC_FORM_RATE_LIMIT', '10/h')
        max_count = int(limit.split('/')[0]) if '/' in limit else 10
        if count >= max_count:
            messages.error(request, 'Too many submissions. Please try again later.')
            return self.render_to_response(self.get_context_data())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        invitation = form.save(commit=False)
        # Set default agency (first active, or create DECD)
        agency = Agency.objects.filter(is_active=True).first()
        if not agency:
            agency = Agency.objects.create(name='Default Agency', abbreviation='DEFAULT')
        invitation.agency = agency
        invitation.status = 'received'
        invitation.save()

        # Handle file attachment
        attachment = self.request.FILES.get('attachment')
        if attachment:
            if attachment.size <= 10 * 1024 * 1024:  # 10MB limit
                InvitationAttachment.objects.create(
                    invitation=invitation,
                    file=attachment,
                    original_filename=attachment.name,
                    content_type=attachment.content_type or '',
                    size_bytes=attachment.size,
                    uploaded_by_staff=False,
                )

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
