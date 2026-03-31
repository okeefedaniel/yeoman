from django.contrib import admin

from .models import Comment, CommentMention, Thread, ThreadSubscription


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('author', 'body', 'created_at', 'is_deleted')
    fields = ('author', 'body', 'created_at', 'is_deleted')


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'content_type', 'object_id', 'is_locked', 'created_at')
    list_filter = ('is_locked', 'content_type')
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'thread', 'created_at', 'is_deleted')
    list_filter = ('is_deleted', 'created_at')
    readonly_fields = ('thread', 'author', 'parent', 'body', 'body_html', 'created_at', 'updated_at')
