"""
Service layer for vote-related business logic.
"""
from typing import List, Dict, Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from core.models import Event, ProposedDate, DateVote, EventInvite


class VoteService:
    """Service class for handling vote business logic."""
    
    @staticmethod
    def vote_on_date(
        event_id: int, 
        date_id: int, 
        user: User, 
        availability: str
    ) -> Tuple[bool, Dict]:
        """
        Vote on availability for a proposed date.
        User must be invited to the event (or be the owner).
        
        Args:
            event_id: ID of the event.
            date_id: ID of the proposed date.
            user: User voting.
            availability: Availability choice (AVAILABLE, MAYBE, NOT_AVAILABLE).
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        # Check if event exists and user has access
        try:
            event = Event.objects.filter(
                Q(user=user) | Q(invites__invitee=user)
            ).distinct().get(id=event_id)
        except Event.DoesNotExist:
            return False, {"error": "Event not found or you don't have access"}
        
        if event.status == Event.Status.CANCELLED:
            return False, {"error": "Cannot vote on a cancelled event"}
        
        if event.status == Event.Status.CONFIRMED:
            return False, {"error": "Cannot vote on a confirmed event"}
        
        # Check if proposed date exists and belongs to event
        try:
            proposed_date = ProposedDate.objects.get(id=date_id, event=event)
        except ProposedDate.DoesNotExist:
            return False, {"error": "Proposed date not found"}
        
        # Validate availability
        valid_choices = [choice[0] for choice in DateVote.Availability.choices]
        if availability not in valid_choices:
            return False, {
                "error": f"Invalid availability. Must be one of: {', '.join(valid_choices)}"
            }
        
        # Create or update vote
        try:
            vote, created = DateVote.objects.update_or_create(
                proposed_date=proposed_date,
                user=user,
                defaults={'availability': availability}
            )
            
            from core.serializers import DateVoteSerializer
            serializer = DateVoteSerializer(vote)
            return True, serializer.data
        
        except Exception as e:
            return False, {"error": f"Failed to record vote: {str(e)}"}
    
    @staticmethod
    def get_event_votes(event_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Get all votes for an event.
        User must be owner or invitee to view votes.
        
        Args:
            event_id: ID of the event.
            user: User requesting votes.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        # Check if event exists and user has access
        try:
            event = Event.objects.filter(
                Q(user=user) | Q(invites__invitee=user)
            ).distinct().get(id=event_id)
        except Event.DoesNotExist:
            return False, {"error": "Event not found or you don't have access"}
        
        # Get all proposed dates with their votes
        proposed_dates = event.proposed_dates.all().prefetch_related('votes', 'votes__user')
        
        result = []
        for proposed_date in proposed_dates:
            votes = proposed_date.votes.all()
            date_data = {
                'proposed_date_id': proposed_date.id,
                'date': proposed_date.date.isoformat(),
                'votes': [
                    {
                        'user_id': vote.user.id,
                        'username': vote.user.username,
                        'availability': vote.availability
                    }
                    for vote in votes
                ],
                'summary': {
                    'available': votes.filter(availability=DateVote.Availability.AVAILABLE).count(),
                    'maybe': votes.filter(availability=DateVote.Availability.MAYBE).count(),
                    'not_available': votes.filter(availability=DateVote.Availability.NOT_AVAILABLE).count(),
                    'total': votes.count()
                }
            }
            result.append(date_data)
        
        return True, result
    
    @staticmethod
    def get_user_votes_for_event(event_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Get the current user's votes for an event.
        
        Args:
            event_id: ID of the event.
            user: User whose votes to retrieve.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        # Check if event exists and user has access
        try:
            event = Event.objects.filter(
                Q(user=user) | Q(invites__invitee=user)
            ).distinct().get(id=event_id)
        except Event.DoesNotExist:
            return False, {"error": "Event not found or you don't have access"}
        
        # Get user's votes for this event
        votes = DateVote.objects.filter(
            proposed_date__event=event,
            user=user
        ).select_related('proposed_date')
        
        from core.serializers import DateVoteSerializer
        serializer = DateVoteSerializer(votes, many=True)
        return True, serializer.data
    
    @staticmethod
    def delete_vote(event_id: int, date_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Delete a user's vote for a proposed date.
        
        Args:
            event_id: ID of the event.
            date_id: ID of the proposed date.
            user: User whose vote to delete.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        # Check if event exists and user has access
        try:
            event = Event.objects.filter(
                Q(user=user) | Q(invites__invitee=user)
            ).distinct().get(id=event_id)
        except Event.DoesNotExist:
            return False, {"error": "Event not found or you don't have access"}
        
        if event.status == Event.Status.CANCELLED:
            return False, {"error": "Cannot modify votes on a cancelled event"}
        
        if event.status == Event.Status.CONFIRMED:
            return False, {"error": "Cannot modify votes on a confirmed event"}
        
        # Check if proposed date exists
        try:
            proposed_date = ProposedDate.objects.get(id=date_id, event=event)
        except ProposedDate.DoesNotExist:
            return False, {"error": "Proposed date not found"}
        
        # Delete the vote
        try:
            vote = DateVote.objects.get(proposed_date=proposed_date, user=user)
            vote.delete()
            return True, {"message": "Vote deleted successfully"}
        except DateVote.DoesNotExist:
            return False, {"error": "Vote not found"}
