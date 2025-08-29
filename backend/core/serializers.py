from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for Event model.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    event_name = serializers.CharField(max_length=255, required=True)
    date = serializers.DateField(required=True, format='%Y-%m-%d', input_formats=['%Y-%m-%d'])
    
    class Meta:
        model = Event
        fields = ['id', 'event_name', 'user', 'date']
        read_only_fields = ['id', 'user']
    
    def create(self, validated_data):
        """
        Create a new event with the authenticated user.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_event_name(self, value):
        """
        Validate event name.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Event name cannot be empty.")
        return value.strip()


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
    
    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class BulkEventCreateSerializer(serializers.Serializer):
    """
    Serializer for creating multiple events at once.
    """
    event_name = serializers.CharField(max_length=255, required=True)
    dates = serializers.ListField(
        child=serializers.DateField(format='%Y-%m-%d', input_formats=['%Y-%m-%d']),
        required=True,
        min_length=1,
        allow_empty=False
    )
    
    def validate_event_name(self, value):
        """
        Validate event name.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Event name cannot be empty.")
        return value.strip()
    
    def validate_dates(self, value):
        """
        Validate dates list.
        """
        if not value:
            raise serializers.ValidationError("At least one date is required.")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_dates = []
        for date in value:
            if date not in seen:
                seen.add(date)
                unique_dates.append(date)
        
        return unique_dates