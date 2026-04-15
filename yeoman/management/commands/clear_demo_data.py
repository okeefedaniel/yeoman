"""
Remove demo content created by `seed_data` from a Yeoman instance.

Safe to run on production: identifies demo rows by the exact seed fingerprints
(submitter emails, demo usernames, demo tag slugs) rather than by agency, so
real invitations attached to the same agency are preserved.

Usage:
    python manage.py clear_demo_data            # dry-run by default
    python manage.py clear_demo_data --apply    # actually delete
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from keel.accounts.models import ProductAccess
from yeoman.models import Invitation, InvitationTag

User = get_user_model()

DEMO_SUBMITTER_EMAILS = {
    'jane@cttech.org',
    'mayor@newhavenct.gov',
    'schen@uconn.edu',
    'troberts@ctbusiness.org',
    'mgarcia@hartford.gov',
    'jwilson@sikorsky.com',
    'ebrown@yale.edu',
    'rkim@stamfordct.gov',
    'lpark@ctinnovation.org',
    'drusso@electricboat.com',
}

DEMO_USERNAMES = {'jscheduler', 'bviewer', 'ddelegate'}

DEMO_TAG_SLUGS = {
    'legislative', 'economic-dev', 'education', 'infrastructure',
    'healthcare', 'technology', 'housing', 'energy',
}


class Command(BaseCommand):
    help = 'Remove demo invitations, users, and tags created by seed_data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually delete rows. Without this flag, runs as a dry-run.',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        label = 'DELETING' if apply else 'DRY-RUN (use --apply to delete)'
        self.stdout.write(self.style.WARNING(f"clear_demo_data: {label}\n"))

        with transaction.atomic():
            invs = Invitation.objects.filter(submitter_email__in=DEMO_SUBMITTER_EMAILS)
            self.stdout.write(f"  Invitations matching demo submitters: {invs.count()}")
            for inv in invs[:5]:
                self.stdout.write(f"    - {inv.pk} {inv.event_name} <{inv.submitter_email}>")
            if apply:
                invs.delete()

            demo_tags = InvitationTag.objects.filter(slug__in=DEMO_TAG_SLUGS)
            unused_tags = [t for t in demo_tags if not t.invitation_set.exists()]
            self.stdout.write(
                f"  Demo tags total={demo_tags.count()} unused={len(unused_tags)}"
            )
            if apply:
                for t in unused_tags:
                    t.delete()

            demo_users = User.objects.filter(username__in=DEMO_USERNAMES)
            self.stdout.write(f"  Demo users: {demo_users.count()}")
            for u in demo_users:
                self.stdout.write(f"    - {u.username} ({u.email})")
            if apply:
                ProductAccess.objects.filter(user__in=demo_users).delete()
                demo_users.delete()

            if not apply:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("\nDone."))
