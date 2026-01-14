"""
Main URL configuration for the core app.
Aggregates URLs from different feature modules.
"""
from django.urls import path, include

# Import URL patterns from feature modules
from .auth import urlpatterns as auth
from .event import urlpatterns as event
from .event_invite import urlpatterns as event_invite
from .vote import urlpatterns as vote

# Combine all URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/', include((auth, 'auth'), namespace='auth')),
    
    # Event management endpoints (includes proposed dates)
    path('events/', include((event, 'events'), namespace='events')),
    
    # Event invite management endpoints
    path('invites/', include((event_invite, 'event_invites'), namespace='event_invites')),
    
    # Vote management endpoints
    path('votes/', include((vote, 'votes'), namespace='votes')),
]
