"""
URL patterns for event-related endpoints.
Includes event CRUD and proposed date management.
"""
from django.urls import path
from ..views import event

app_name = 'events'

urlpatterns = [
    # Event CRUD
    path('', event.list_events, name='list'),
    path('create/', event.create_event, name='create'),
    path('<int:event_id>/', event.get_event, name='detail'),
    path('<int:event_id>/update/', event.update_event, name='update'),
    path('<int:event_id>/delete/', event.delete_event, name='delete'),
    
    # Event status management
    path('<int:event_id>/confirm/', event.confirm_event, name='confirm'),
    path('<int:event_id>/cancel/', event.cancel_event, name='cancel'),
    
    # Proposed dates management
    path('<int:event_id>/dates/', event.list_proposed_dates, name='list_dates'),
    path('<int:event_id>/dates/add/', event.add_proposed_date, name='add_date'),
    path('<int:event_id>/dates/<int:date_id>/delete/', event.remove_proposed_date, name='remove_date'),
]
