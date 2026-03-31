from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Keel User model stub. In production, this comes from keel.auth
    with SSO, MFA, and role management.
    """
    org = models.ForeignKey(
        'keel_orgs.Organization',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
    )

    class Meta:
        db_table = 'keel_auth_user'

    def __str__(self):
        return self.get_full_name() or self.username

    def has_role(self, role_name, org=None):
        """Check if user has a specific role, optionally scoped to an org."""
        target_org = org or self.org
        if not target_org:
            return False
        return self.role_assignments.filter(
            role__name=role_name,
            org=target_org,
        ).exists()

    def get_roles(self, org=None):
        """Get all role names for this user in an org."""
        target_org = org or self.org
        if not target_org:
            return []
        return list(
            self.role_assignments.filter(org=target_org)
            .values_list('role__name', flat=True)
        )


class Role(models.Model):
    """Named role (e.g. yeoman_admin, yeoman_scheduler)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'keel_auth_role'

    def __str__(self):
        return self.name


class RoleAssignment(models.Model):
    """Assigns a role to a user within an organization."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='role_assignments'
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name='assignments'
    )
    org = models.ForeignKey(
        'keel_orgs.Organization', on_delete=models.CASCADE,
        related_name='role_assignments',
    )

    class Meta:
        db_table = 'keel_auth_role_assignment'
        unique_together = ('user', 'role', 'org')

    def __str__(self):
        return f"{self.user} → {self.role} @ {self.org}"
