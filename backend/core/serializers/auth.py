"""
Serializers for authentication-related views.
"""
from rest_framework import serializers
from django.contrib.auth.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for User registration.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=1)
    username = serializers.CharField(required=True, min_length=1, max_length=150)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        read_only_fields = ['id']


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
