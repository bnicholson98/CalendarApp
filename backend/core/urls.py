from django.urls import path
from .views import calendar_events

urlpatterns = [
    path('events/', calendar_events),
]
