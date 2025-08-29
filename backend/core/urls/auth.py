"""
URL patterns for authentication-related endpoints.
"""
from django.urls import path
from ..views import auth

app_name = 'auth'

urlpatterns = [
    path('register/', auth.register_user, name='register'),
    path('login/', auth.login_user, name='login'),
    path('logout/', auth.logout_user, name='logout'),
]
