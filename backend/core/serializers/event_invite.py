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
    invitee_username = serializers.CharField(source='invitee.username', read_only=True)
    status = serializers.ChoiceField(choices=EventInvite.Status.choices, read_only=True)
    
    class Meta:
        model = EventInvite
        fields = ['id', 'event', 'owner', 'invitee', 'invitee_username', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'event', 'owner', 'invitee', 'invitee_username', 'status', 'created_at', 'updated_at']


class EventInviteCreateSerializer(serializers.Serializer):
    """
    Serializer for creating an event invite by username.
    """
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    username = serializers.CharField(required=True)
    
    def validate(self, data):
        """
        Validate the invite data: resolve username to a User, then check
        ownership, self-invite, and duplicate constraints.
        """
        request = self.context.get('request')
        event = data.get('event')
        username = data.get('username', '').strip()

        # Only event owner can create invites
        if event and request and event.user != request.user:
            raise serializers.ValidationError(
                {"event": "Only the event owner can create invites."}
            )

        try:
            invitee = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"username": "No user found with that username."}
            )

        # Owner cannot invite themselves
        if request and invitee == request.user:
            raise serializers.ValidationError(
                {"username": "You cannot invite yourself."}
            )

        # Check for duplicate invite
        if event:
            if EventInvite.objects.filter(event=event, invitee=invitee).exists():
                raise serializers.ValidationError(
                    {"username": "This user has already been invited to this event."}
                )

        data['invitee'] = invitee
        return data


class InviteStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an invite status.
    """
    status = serializers.ChoiceField(
        choices=EventInvite.Status.choices,
        required=True
    )
