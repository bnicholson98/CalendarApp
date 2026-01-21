from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, EventInvite, ProposedDate, DateVote


class ProposedDateSerializer(serializers.ModelSerializer):
    """
    Serializer for ProposedDate model.
    """
    vote_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ProposedDate
        fields = ['id', 'event', 'date', 'created_at', 'vote_summary']
        read_only_fields = ['id', 'event', 'created_at', 'vote_summary']
    
    def get_vote_summary(self, obj):
        """Get vote counts for this proposed date."""
        votes = obj.votes.all()
        return {
            'available': votes.filter(availability=DateVote.Availability.AVAILABLE).count(),
            'maybe': votes.filter(availability=DateVote.Availability.MAYBE).count(),
            'not_available': votes.filter(availability=DateVote.Availability.NOT_AVAILABLE).count(),
            'total': votes.count()
        }


class DateVoteSerializer(serializers.ModelSerializer):
    """
    Serializer for DateVote model.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DateVote
        fields = ['id', 'proposed_date', 'user', 'username', 'availability', 'created_at', 'updated_at']
        read_only_fields = ['id', 'proposed_date', 'user', 'username', 'created_at', 'updated_at']
    
    def validate_availability(self, value):
        """Validate availability value."""
        valid_choices = [choice[0] for choice in DateVote.Availability.choices]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Invalid availability. Must be one of: {', '.join(valid_choices)}"
            )
        return value


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for Event model.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    event_name = serializers.CharField(max_length=255, required=True)
    proposed_dates = ProposedDateSerializer(many=True, read_only=True)
    confirmed_date = ProposedDateSerializer(read_only=True)
    status = serializers.ChoiceField(choices=Event.Status.choices, read_only=True)
    
    class Meta:
        model = Event
        fields = ['id', 'event_name', 'user', 'status', 'proposed_dates', 'confirmed_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'status', 'proposed_dates', 'confirmed_date', 'created_at', 'updated_at']
    
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


class EventCreateSerializer(serializers.Serializer):
    """
    Serializer for creating an event proposal with multiple dates and optional invitees.
    """
    event_name = serializers.CharField(max_length=255, required=True)
    proposed_dates = serializers.ListField(
        child=serializers.DateField(format='%Y-%m-%d', input_formats=['%Y-%m-%d']),
        required=True,
        min_length=1,
        allow_empty=False
    )
    invitees = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    
    def validate_event_name(self, value):
        """
        Validate event name.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Event name cannot be empty.")
        return value.strip()
    
    def validate_proposed_dates(self, value):
        """
        Validate dates list - remove duplicates while preserving order.
        """
        if not value:
            raise serializers.ValidationError("At least one proposed date is required.")
        
        seen = set()
        unique_dates = []
        for date in value:
            if date not in seen:
                seen.add(date)
                unique_dates.append(date)
        
        return unique_dates
    
    def validate_invitees(self, value):
        """
        Validate invitees list - ensure all user IDs exist.
        """
        if not value:
            return value
        
        existing_users = User.objects.filter(id__in=value).values_list('id', flat=True)
        invalid_ids = set(value) - set(existing_users)
        
        if invalid_ids:
            raise serializers.ValidationError(
                f"Users with IDs {list(invalid_ids)} do not exist."
            )
        
        return list(set(value))  # Remove duplicates
    
    def validate(self, data):
        """
        Cross-field validation.
        """
        request = self.context.get('request')
        invitees = data.get('invitees', [])
        
        # Ensure owner is not in invitees list
        if request and request.user.id in invitees:
            raise serializers.ValidationError(
                {"invitees": "You cannot invite yourself."}
            )
        
        return data


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


class EventInviteSerializer(serializers.ModelSerializer):
    """
    Serializer for EventInvite model.
    """
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    invitee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    status = serializers.ChoiceField(
        choices=EventInvite.Status.choices,
        default=EventInvite.Status.PENDING
    )
    
    class Meta:
        model = EventInvite
        fields = ['id', 'event', 'owner', 'invitee', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate the invite data.
        """
        request = self.context.get('request')
        event = data.get('event')
        invitee = data.get('invitee')
        
        # For updates, get event from instance if not provided
        if self.instance:
            event = event or self.instance.event
            invitee = invitee or self.instance.invitee
        
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
        
        # Check for duplicate invite (only on create)
        if not self.instance and event and invitee:
            if EventInvite.objects.filter(event=event, invitee=invitee).exists():
                raise serializers.ValidationError(
                    {"invitee": "This user has already been invited to this event."}
                )
        
        return data
    
    def create(self, validated_data):
        """
        Create a new event invite with the authenticated user as owner.
        """
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class EventConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming an event with a specific proposed date.
    """
    proposed_date_id = serializers.IntegerField(required=True)
    
    def validate_proposed_date_id(self, value):
        """
        Validate that the proposed date exists and belongs to the event.
        """
        event = self.context.get('event')
        
        if not event:
            raise serializers.ValidationError("Event context is required.")
        
        try:
            proposed_date = ProposedDate.objects.get(id=value, event=event)
        except ProposedDate.DoesNotExist:
            raise serializers.ValidationError(
                "Proposed date not found or does not belong to this event."
            )
        
        return value


class ProposedDateCreateSerializer(serializers.Serializer):
    """
    Serializer for adding a proposed date to an event.
    """
    date = serializers.DateField(
        required=True,
        format='%Y-%m-%d',
        input_formats=['%Y-%m-%d']
    )


class VoteCreateSerializer(serializers.Serializer):
    """
    Serializer for creating/updating a vote on a proposed date.
    """
    availability = serializers.ChoiceField(
        choices=DateVote.Availability.choices,
        required=True
    )


class InviteStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an invite status.
    """
    status = serializers.ChoiceField(
        choices=EventInvite.Status.choices,
        required=True
    )
