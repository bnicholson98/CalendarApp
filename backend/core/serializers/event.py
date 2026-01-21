"""
Serializers for event-related views.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import Event, ProposedDate, DateVote


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


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for Event model - used for read operations.
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
        
        return list(set(value)) 
    
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


class EventUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an event.
    """
    event_name = serializers.CharField(max_length=255, required=False)
    
    def validate_event_name(self, value):
        """
        Validate event name.
        """
        if value is not None and (not value or not value.strip()):
            raise serializers.ValidationError("Event name cannot be empty.")
        return value.strip() if value else value


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
        
        if event.status == Event.Status.CONFIRMED:
            raise serializers.ValidationError("Event is already confirmed")
        
        if event.status == Event.Status.CANCELLED:
            raise serializers.ValidationError("Cannot confirm a cancelled event")

        try:
            ProposedDate.objects.get(id=value, event=event)
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
