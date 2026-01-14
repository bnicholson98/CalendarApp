"""
URL patterns for event invite-related endpoints.
"""
from django.urls import path
from ..views import event_invite

app_name = 'event_invites'

urlpatterns = [
    path('', event_invite.list_received_invites, name='list_received'),
    path('sent/', event_invite.list_sent_invites, name='list_sent'),
    path('create/', event_invite.create_invite, name='create'),
    path('<int:invite_id>/', event_invite.get_invite, name='detail'),
    path('<int:invite_id>/update/', event_invite.update_invite_status, name='update'),
    path('<int:invite_id>/delete/', event_invite.delete_invite, name='delete'),
]
