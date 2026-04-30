"""Tests for yeoman.helm_inbox.yeoman_helm_feed_inbox.

Pins the open-status filter to the canonical workflow values defined in
``yeoman.workflow.INVITATION_WORKFLOW``. The original implementation used
``in_review`` (a value that does not exist in the workflow), which silently
hid every triage-state invitation from Helm's "Awaiting Me" column.
"""
import json

from allauth.socialaccount.models import SocialAccount
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings

from keel.accounts.models import Agency, KeelUser

from yeoman.helm_inbox import yeoman_helm_feed_inbox
from yeoman.models import Invitation


@override_settings(HELM_FEED_API_KEY='k', DEMO_MODE=False)
class HelmInboxStatusFilterTests(TestCase):
    """Regression coverage for the under_review status filter."""

    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()
        self.agency = Agency.objects.create(name='Test', abbreviation='TST')

    def tearDown(self):
        cache.clear()

    def _make_user(self, sub, username):
        user = KeelUser.objects.create_user(
            username=username, email=f'{username}@t.local', agency=self.agency,
        )
        SocialAccount.objects.create(user=user, provider='keel', uid=sub)
        return user

    def _make_invitation(self, status, **kwargs):
        return Invitation.objects.create(
            agency=self.agency,
            status=status,
            submitter_first_name='S',
            submitter_last_name='T',
            submitter_email='s@t.local',
            event_name=f'Event-{status}',
            event_format='presentation',
            **kwargs,
        )

    def _call(self, user_sub):
        return yeoman_helm_feed_inbox(
            self.rf.get(
                f'/api/v1/helm-feed/inbox/?user_sub={user_sub}',
                HTTP_AUTHORIZATION='Bearer k',
            ),
        )

    def test_under_review_invitation_surfaces_in_inbox(self):
        """Regression: 'under_review' invitations must appear in the user's inbox.

        Before the fix, the filter listed 'in_review' (a non-existent status),
        so every triage-state invitation was silently dropped from Helm.
        """
        user = self._make_user(sub='sub-under', username='ur')
        inv = self._make_invitation(status='under_review', assigned_to=user)

        resp = self._call('sub-under')
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        ids = [item['id'] for item in body['items']]
        self.assertIn(str(inv.pk), ids)

    def test_terminal_invitation_excluded(self):
        """Sanity check: completed/declined invitations stay out of the inbox."""
        user = self._make_user(sub='sub-done', username='done')
        open_inv = self._make_invitation(status='received', assigned_to=user)
        completed = self._make_invitation(status='completed', assigned_to=user)
        declined = self._make_invitation(status='declined', assigned_to=user)

        body = json.loads(self._call('sub-done').content)
        ids = {item['id'] for item in body['items']}
        self.assertIn(str(open_inv.pk), ids)
        self.assertNotIn(str(completed.pk), ids)
        self.assertNotIn(str(declined.pk), ids)
