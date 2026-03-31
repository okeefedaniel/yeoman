from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Comment, Thread, ThreadSubscription
from .services import add_comment, invite_to_discuss

User = get_user_model()


@login_required
@require_POST
def add_comment_view(request, content_type_id, object_id):
    """Add a comment to a thread. Returns htmx partial."""
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'Comment body is required.'}, status=400)

    ct = get_object_or_404(ContentType, pk=content_type_id)
    model_class = ct.model_class()
    target_obj = get_object_or_404(model_class, pk=object_id)

    comment = add_comment(target_obj, request.user, body)

    return render(request, 'keel/collaboration/partials/comment.html', {
        'comment': comment,
        'user': request.user,
    })


@login_required
@require_POST
def reply_to_comment_view(request, comment_id):
    """Reply to a specific comment. Returns htmx partial."""
    parent = get_object_or_404(Comment, pk=comment_id)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'Reply body is required.'}, status=400)

    target_obj = parent.thread.target
    comment = add_comment(target_obj, request.user, body, parent=parent)

    return render(request, 'keel/collaboration/partials/comment.html', {
        'comment': comment,
        'user': request.user,
    })


@login_required
@require_POST
def invite_to_discuss_view(request, content_type_id, object_id):
    """Invite users to discuss a target object."""
    ct = get_object_or_404(ContentType, pk=content_type_id)
    model_class = ct.model_class()
    target_obj = get_object_or_404(model_class, pk=object_id)

    user_ids = request.POST.getlist('user_ids')
    message = request.POST.get('message', '').strip()

    invitees = User.objects.filter(pk__in=user_ids)
    invite_to_discuss(target_obj, request.user, invitees, message or None)

    return JsonResponse({'ok': True})


@login_required
@require_POST
def manage_subscription_view(request, thread_id):
    """Subscribe/unsubscribe/mute a thread."""
    thread = get_object_or_404(Thread, pk=thread_id)
    action = request.POST.get('action', 'subscribe')

    if action == 'subscribe':
        ThreadSubscription.objects.get_or_create(
            thread=thread, user=request.user,
        )
    elif action == 'unsubscribe':
        ThreadSubscription.objects.filter(
            thread=thread, user=request.user,
        ).delete()
    elif action == 'mute':
        sub, _ = ThreadSubscription.objects.get_or_create(
            thread=thread, user=request.user,
        )
        sub.is_muted = True
        sub.save(update_fields=['is_muted'])
    elif action == 'unmute':
        ThreadSubscription.objects.filter(
            thread=thread, user=request.user,
        ).update(is_muted=False)

    return JsonResponse({'ok': True, 'action': action})


@login_required
@require_POST
def delete_comment_view(request, comment_id):
    """Soft-delete a comment. Author or admin only."""
    comment = get_object_or_404(Comment, pk=comment_id)

    is_author = comment.author == request.user
    is_admin = request.user.has_role('yeoman_admin')

    if not (is_author or is_admin):
        return HttpResponseForbidden("You cannot delete this comment.")

    comment.is_deleted = True
    comment.deleted_at = timezone.now()
    comment.deleted_by = request.user
    comment.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    return JsonResponse({'ok': True, 'comment_id': comment_id})
