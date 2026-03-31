import uuid

from django.db import models


class Organization(models.Model):
    """
    Keel Organization stub. In production, comes from keel.orgs
    with full multi-tenancy, billing, and settings.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'keel_orgs_organization'

    def __str__(self):
        return self.name
