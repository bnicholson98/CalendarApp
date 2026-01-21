"""
Serializers for event invite-related views.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import Event, EventInvite


class EventInviteSerializer(serializers.ModelSerializer):
    """
    Serializer for EventInvite model - used for read operations.
    """
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    event = serializers.PrimaryKeyRelatedField(read_only=True)
    invitee = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.ChoiceField(choices=EventInvite.Status.choices, read_only=True)
    
    class Meta:
        model = EventInvite
        fields = ['id', 'event', 'owner', 'invitee', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'event', 'owner', 'invitee', 'status', 'created_at', 'updated_at']


class EventInviteCreateSerializer(serializers.Serializer):
    """
    Serializer for creating an event invite.
    """
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    invitee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    def validate(self, data):
        """
        Validate the invite data.
        """
        request = self.context.get('request')
        event = data.get('event')
        invitee = data.get('invitee')
        
        # Only event owner can create invites
        if event and request and event.user != request.user:
            raise serializers.ValidationError(
                {"event": "Only the event owner can create invites."}
            )
        
        # Owner cannot invite themselves
        if invitee and request and invitee == request.user:
            raise serializers.ValidationError(
                {"invitee": "You cannot invite yourself."}
            )
        
        # Check for duplicate invite
        if event and invitee:
            if EventInvite.objects.filter(event=event, invitee=invitee).exists():
                raise serializers.ValidationError(
                    {"invitee": "This user has already been invited to this event."}
                )
        
        return data


class InviteStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an invite status.
    """
    status = serializers.ChoiceField(
        choices=EventInvite.Status.choices,
        required=True
    )
