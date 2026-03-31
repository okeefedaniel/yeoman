import re

import bleach
import markdown
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from keel.notifications.dispatch import notify

from .models import Comment, CommentMention, Thread, ThreadSubscription

User = get_user_model()


def parse_mentions(body):
    """Parse @username mentions from comment body. Returns list of User objects."""
    pattern = r'@(\w+)'
    usernames = re.findall(pattern, body)
    if not usernames:
        return []
    return list(User.objects.filter(username__in=usernames))


def render_comment_body(body):
    """Render markdown body to sanitized HTML."""
    html = markdown.markdown(body, extensions=['nl2br'])
    allowed_tags = ['p', 'br', 'strong', 'em', 'a', 'code', 'pre', 'ul', 'ol', 'li']
    allowed_attrs = {'a': ['href', 'title']}
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)


def add_comment(target_obj, author, body, parent=None):
    """
    Add a comment to any model instance.
    Creates Thread if it doesn't exist.
    Parses @mentions from body.
    Auto-subscribes author.
    Notifies all thread subscribers (except author).
    """
    ct = ContentType.objects.get_for_model(target_obj)
    thread, _ = Thread.objects.get_or_create(
        content_type=ct,
        object_id=target_obj.pk,
    )

    if thread.is_locked:
        raise PermissionError("Thread is locked.")

    mentions = parse_mentions(body)
    html = render_comment_body(body)

    comment = Comment.objects.create(
        thread=thread,
        author=author,
        parent=parent,
        body=body,
        body_html=html,
    )

    for user in mentions:
        CommentMention.objects.get_or_create(comment=comment, mentioned_user=user)
        ThreadSubscription.objects.get_or_create(thread=thread, user=user)

    ThreadSubscription.objects.get_or_create(thread=thread, user=author)

    subscribers = thread.subscriptions.filter(
        is_muted=False
    ).exclude(user=author).select_related('user')

    for sub in subscribers:
        notify(
            recipient=sub.user,
            template_slug='collaboration_new_comment',
            context={
                'author': str(author),
                'comment_body': comment.body[:200],
                'target': str(target_obj),
            },
            channels=['in_app', 'email'],
        )

    return comment


def get_thread(target_obj):
    """Get thread for a target object. Returns None if no thread exists."""
    ct = ContentType.objects.get_for_model(target_obj)
    try:
        return Thread.objects.get(content_type=ct, object_id=target_obj.pk)
    except Thread.DoesNotExist:
        return None


def invite_to_discuss(target_obj, inviter, invitees, message=None):
    """
    Invite users to discuss a target object.
    Creates thread if needed, subscribes invitees, sends notification.
    """
    ct = ContentType.objects.get_for_model(target_obj)
    thread, _ = Thread.objects.get_or_create(
        content_type=ct,
        object_id=target_obj.pk,
    )

    for user in invitees:
        ThreadSubscription.objects.get_or_create(thread=thread, user=user)
        notify(
            recipient=user,
            template_slug='collaboration_invited_to_discuss',
            context={
                'inviter': str(inviter),
                'target': str(target_obj),
                'message': message or '',
            },
            channels=['in_app', 'email'],
        )

    if message:
        add_comment(target_obj, inviter, message)

    return thread
