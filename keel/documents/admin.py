from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'content_type', 'size_bytes', 'uploaded_by', 'created_at')
    readonly_fields = ('id', 'created_at')
