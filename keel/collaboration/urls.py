from django.urls import path

from . import views

app_name = 'collaboration'

urlpatterns = [
    path(
        'thread/<int:content_type_id>/<uuid:object_id>/comment/',
        views.add_comment_view,
        name='add_comment',
    ),
    path(
        'comment/<int:comment_id>/reply/',
        views.reply_to_comment_view,
        name='reply',
    ),
    path(
        'thread/<int:content_type_id>/<uuid:object_id>/invite/',
        views.invite_to_discuss_view,
        name='invite',
    ),
    path(
        'thread/<int:thread_id>/subscription/',
        views.manage_subscription_view,
        name='subscription',
    ),
    path(
        'comment/<int:comment_id>/delete/',
        views.delete_comment_view,
        name='delete_comment',
    ),
]
