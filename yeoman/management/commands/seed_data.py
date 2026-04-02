"""
Management command to seed Yeoman with demo data.
Usage: python manage.py seed_data
"""
import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from keel.accounts.models import Agency, ProductAccess
from yeoman.models import Invitation, InvitationTag

User = get_user_model()

# Role constants (must match PRODUCT_ROLES in keel/accounts/models.py)
ROLE_ADMIN = 'yeoman_admin'
ROLE_SCHEDULER = 'yeoman_scheduler'
ROLE_VIEWER = 'yeoman_viewer'
ROLE_DELEGATE = 'yeoman_delegate'


class Command(BaseCommand):
    help = 'Seed Yeoman with demo agency, users, tags, and sample invitations.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Yeoman data...\n")

        # 1. Agency
        agency, created = Agency.objects.get_or_create(
            abbreviation='DECD',
            defaults={'name': 'CT Department of Economic and Community Development'},
        )
        self.stdout.write(f"  Agency: {agency.name} ({'created' if created else 'exists'})")

        # 2. Users (one per role) + ProductAccess
        users = {}
        user_defs = [
            ('dokeefe', 'Dan', "O'Keefe", ROLE_ADMIN),
            ('jscheduler', 'Jane', 'Scheduler', ROLE_SCHEDULER),
            ('bviewer', 'Bob', 'Viewer', ROLE_VIEWER),
            ('ddelegate', 'Diana', 'Delegate', ROLE_DELEGATE),
        ]
        for username, first, last, role in user_defs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@decd.ct.gov',
                    'is_staff': role in (ROLE_ADMIN, ROLE_SCHEDULER),
                    'agency': agency,
                },
            )
            if created:
                user.set_password('yeoman2026')
                user.save()

            # Ensure ProductAccess exists for this user
            ProductAccess.objects.get_or_create(
                user=user,
                product='yeoman',
                defaults={'role': role, 'is_active': True},
            )

            users[role] = user
            self.stdout.write(f"  User: {user} ({role}) ({'created' if created else 'exists'})")

        # Make admin a superuser for Django admin access
        admin_user = users[ROLE_ADMIN]
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()

        # 3. Tags
        tag_defs = [
            ('Legislative', 'legislative', '#0d6efd'),
            ('Economic Development', 'economic-dev', '#198754'),
            ('Education', 'education', '#6f42c1'),
            ('Infrastructure', 'infrastructure', '#fd7e14'),
            ('Healthcare', 'healthcare', '#dc3545'),
            ('Technology', 'technology', '#20c997'),
            ('Housing', 'housing', '#6610f2'),
            ('Energy', 'energy', '#ffc107'),
        ]
        tags = {}
        for name, slug, color in tag_defs:
            tag, _ = InvitationTag.objects.get_or_create(
                agency=agency, slug=slug,
                defaults={'name': name, 'color': color},
            )
            tags[slug] = tag
        self.stdout.write(f"  Tags: {len(tags)} created/verified")

        # 4. Sample Invitations (20 across all statuses)
        today = date.today()
        ct_locations = [
            ('Connecticut Convention Center', '100 Columbus Blvd', 'Hartford', 'CT', '06103', Decimal('41.7627'), Decimal('-72.6700')),
            ('Yale University', '149 Elm St', 'New Haven', 'CT', '06511', Decimal('41.3113'), Decimal('-72.9246')),
            ('Mohegan Sun', '1 Mohegan Sun Blvd', 'Uncasville', 'CT', '06382', Decimal('41.4282'), Decimal('-72.0870')),
            ('UConn Storrs', '2131 Hillside Rd', 'Storrs', 'CT', '06269', Decimal('41.8077'), Decimal('-72.2540')),
            ('Stamford Innovation Center', '175 Atlantic St', 'Stamford', 'CT', '06901', Decimal('41.0534'), Decimal('-73.5387')),
            ('New London City Hall', '181 State St', 'New London', 'CT', '06320', Decimal('41.3557'), Decimal('-72.0995')),
            ('Waterbury City Hall', '236 Grand St', 'Waterbury', 'CT', '06702', Decimal('41.5582'), Decimal('-73.0440')),
            ('Bridgeport Discovery Museum', '4450 Park Ave', 'Bridgeport', 'CT', '06604', Decimal('41.2128'), Decimal('-73.2096')),
            ('Norwalk City Hall', '125 East Ave', 'Norwalk', 'CT', '06851', Decimal('41.1177'), Decimal('-73.4082')),
            ('Danbury Fair Mall', '7 Backus Ave', 'Danbury', 'CT', '06810', Decimal('41.4041'), Decimal('-73.4540')),
        ]

        formats = [c[0] for c in Invitation.FORMAT_CHOICES]
        modalities = ['in_person', 'virtual', 'hybrid']
        priorities = ['low', 'normal', 'normal', 'normal', 'high', 'urgent']
        statuses_to_seed = [
            'received', 'received', 'received',
            'under_review', 'under_review', 'under_review', 'under_review', 'under_review',
            'needs_info', 'needs_info',
            'accepted', 'accepted',
            'declined',
            'delegated', 'delegated',
            'scheduled', 'scheduled', 'scheduled',
            'completed',
            'cancelled',
        ]

        submitters = [
            ('Jane Smith', 'jane@cttech.org', 'CT Tech Council', 'Executive Director'),
            ('Mayor Lee', 'mayor@newhavenct.gov', 'City of New Haven', 'Mayor'),
            ('Sarah Chen', 'schen@uconn.edu', 'UConn', 'Dean of Engineering'),
            ('Tom Roberts', 'troberts@ctbusiness.org', 'CT Business Council', 'President'),
            ('Maria Garcia', 'mgarcia@hartford.gov', 'City of Hartford', 'Economic Dev Director'),
            ('James Wilson', 'jwilson@sikorsky.com', 'Sikorsky Aircraft', 'VP Government Relations'),
            ('Emily Brown', 'ebrown@yale.edu', 'Yale University', 'Associate Provost'),
            ('Robert Kim', 'rkim@stamfordct.gov', 'City of Stamford', 'Mayor'),
            ('Lisa Park', 'lpark@ctinnovation.org', 'CT Innovation Fund', 'CEO'),
            ('David Russo', 'drusso@electricboat.com', 'Electric Boat', 'Director of Community Affairs'),
        ]

        event_names = [
            'CT Innovation Summit 2026',
            'Ribbon Cutting: New Manufacturing Lab',
            'Annual Economic Development Conference',
            'Small Business Roundtable',
            "Governor's STEM Education Panel",
            'Aerospace Industry Tour',
            'Healthcare Innovation Forum',
            'Housing Affordability Town Hall',
            'Clean Energy Keynote',
            'Legislative Breakfast',
            'Workforce Development Summit',
            'Biotech Incubator Grand Opening',
            'Municipal Leaders Roundtable',
            'Digital Economy Panel',
            'Veterans Employment Fair',
            'Rural Broadband Forum',
            'Transportation Infrastructure Review',
            'Youth Entrepreneurship Awards',
            'Green Building Ribbon Cutting',
            'Defense Industry Fireside Chat',
        ]

        tag_keys = list(tags.keys())
        existing = Invitation.objects.filter(agency=agency).count()
        if existing >= 20:
            self.stdout.write(f"  Invitations: {existing} already exist, skipping seed")
        else:
            for i, status in enumerate(statuses_to_seed):
                loc = ct_locations[i % len(ct_locations)]
                sub = submitters[i % len(submitters)]
                modality = random.choice(modalities)
                event_date = today + timedelta(days=random.randint(-30, 90))

                inv = Invitation.objects.create(
                    agency=agency,
                    submitter_first_name=sub[0].split()[0],
                    submitter_last_name=' '.join(sub[0].split()[1:]),
                    submitter_email=sub[1],
                    submitter_organization=sub[2],
                    submitter_title=sub[3],
                    event_name=event_names[i],
                    event_description=f"Join us for {event_names[i]}. This event brings together leaders from across Connecticut.",
                    event_date=event_date,
                    event_time_start=time(9 + (i % 8), 0),
                    event_time_end=time(10 + (i % 8), 30),
                    event_format=formats[i % len(formats)],
                    modality=modality,
                    venue_name=loc[0] if modality != 'virtual' else '',
                    venue_address=loc[1] if modality != 'virtual' else '',
                    venue_city=loc[2] if modality != 'virtual' else '',
                    venue_state=loc[3] if modality != 'virtual' else '',
                    venue_zip=loc[4] if modality != 'virtual' else '',
                    latitude=loc[5] if modality != 'virtual' else None,
                    longitude=loc[6] if modality != 'virtual' else None,
                    virtual_platform='Zoom' if modality in ('virtual', 'hybrid') else '',
                    virtual_link='https://zoom.us/j/1234567890' if modality in ('virtual', 'hybrid') else '',
                    priority=random.choice(priorities),
                    status=status,
                    assigned_to=users[ROLE_SCHEDULER] if status != 'received' else None,
                    delegated_to=users[ROLE_DELEGATE] if status == 'delegated' else None,
                    delegated_by=users[ROLE_ADMIN] if status == 'delegated' else None,
                    created_by=None,
                )

                # Add 1-2 random tags
                inv_tags = random.sample(tag_keys, min(2, len(tag_keys)))
                inv.tags.set([tags[t] for t in inv_tags])

            self.stdout.write(f"  Invitations: 20 created")

        self.stdout.write(self.style.SUCCESS(
            "\nSeed complete! Login with dokeefe / yeoman2026"
        ))
