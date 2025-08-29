"""
Main URL configuration for the core app.
Aggregates URLs from different feature modules.
"""
from django.urls import path, include

# Import URL patterns from feature modules
from .auth import urlpatterns as auth
from .event import urlpatterns as event

# Combine all URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/', include((auth, 'auth'), namespace='auth')),
    
    # Event management endpoints
    path('events/', include((event, 'events'), namespace='events')),
]
