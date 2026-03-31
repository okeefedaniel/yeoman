from django import template
from django.contrib.contenttypes.models import ContentType

from keel.collaboration.services import get_thread

register = template.Library()


@register.inclusion_tag('keel/collaboration/thread_panel.html', takes_context=True)
def render_thread(context, target_obj):
    """
    Drop-in template tag. Any product can add threaded discussion to any detail page:

        {% load collaboration_tags %}
        {% render_thread invitation %}
    """
    thread = get_thread(target_obj)
    ct = ContentType.objects.get_for_model(target_obj)
    comments = []
    if thread:
        comments = thread.comments.filter(
            is_deleted=False
        ).select_related('author', 'parent')

    return {
        'thread': thread,
        'comments': comments,
        'target': target_obj,
        'content_type_id': ct.pk,
        'object_id': str(target_obj.pk),
        'user': context['request'].user,
    }
