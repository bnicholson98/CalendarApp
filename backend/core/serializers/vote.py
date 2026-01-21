"""
Serializers for vote-related views.
"""
from rest_framework import serializers
from core.models import DateVote


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


class VoteCreateSerializer(serializers.Serializer):
    """
    Serializer for creating/updating a vote on a proposed date.
    """
    availability = serializers.ChoiceField(
        choices=DateVote.Availability.choices,
        required=True
    )
