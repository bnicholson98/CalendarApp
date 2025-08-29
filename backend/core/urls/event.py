"""
URL patterns for event-related endpoints.
"""
from django.urls import path
from ..views import event

app_name = 'events'

urlpatterns = [
    path('', event.list_events, name='list'),
    path('create/', event.create_event, name='create'),
    path('<int:event_id>/', event.get_event, name='detail'),
    path('<int:event_id>/update/', event.update_event, name='update'),
    path('<int:event_id>/delete/', event.delete_event, name='delete'),
]
