"""
URL patterns for vote-related endpoints.
"""
from django.urls import path
from ..views import vote

app_name = 'votes'

urlpatterns = [
    # Voting on proposed dates
    path('events/<int:event_id>/dates/<int:date_id>/', vote.vote_on_date, name='vote'),
    path('events/<int:event_id>/dates/<int:date_id>/delete/', vote.delete_vote, name='delete'),
    
    # View votes
    path('events/<int:event_id>/', vote.get_event_votes, name='list'),
    path('events/<int:event_id>/mine/', vote.get_my_votes, name='my_votes'),
]
