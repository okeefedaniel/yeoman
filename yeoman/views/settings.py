"""Principal profile and reference address settings."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from keel.accounts.models import Agency

from yeoman.forms import PrincipalProfileForm, ReferenceAddressFormSet
from yeoman.models import PrincipalProfile


class PrincipalSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'yeoman/settings_principal.html'

    def _get_profile(self):
        agency = Agency.objects.filter(is_active=True).first()
        if not agency:
            return None, None
        profile, _ = PrincipalProfile.objects.get_or_create(
            agency=agency,
            defaults={'display_name': agency.contact_name or agency.name},
        )
        return agency, profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        agency, profile = self._get_profile()
        ctx['agency'] = agency
        ctx['profile'] = profile

        if 'form' not in kwargs:
            ctx['form'] = PrincipalProfileForm(instance=profile)
        if 'formset' not in kwargs:
            ctx['formset'] = ReferenceAddressFormSet(instance=profile)
        return ctx

    def post(self, request, *args, **kwargs):
        agency, profile = self._get_profile()
        if not profile:
            messages.error(request, 'No active agency found.')
            return redirect(reverse('yeoman:principal_settings'))

        form = PrincipalProfileForm(request.POST, instance=profile)
        formset = ReferenceAddressFormSet(request.POST, instance=profile)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Principal settings saved.')
            return redirect(reverse('yeoman:principal_settings'))

        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )
