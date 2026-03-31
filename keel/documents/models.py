import uuid

from django.conf import settings
from django.db import models


class Document(models.Model):
    """
    Keel Document stub. In production keel.documents, this provides:
    - Virus scanning (ClamAV)
    - S3 / local storage backends
    - Versioning
    - Metadata extraction
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='documents/%Y/%m/')
    original_filename = models.CharField(max_length=500)
    content_type = models.CharField(max_length=255, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'keel_documents_document'

    def __str__(self):
        return self.original_filename
