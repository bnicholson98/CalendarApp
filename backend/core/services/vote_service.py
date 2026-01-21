"""
Service layer for vote-related business logic.
"""
from typing import List, Dict
from django.contrib.auth.models import User
from django.db.models import QuerySet

from core.models import Event, ProposedDate, DateVote
from core.services.event_service import EventService
from core.exceptions import NotFoundError, ValidationError


class VoteService:
    """Service class for handling vote business logic."""
    
    @staticmethod
    def vote_on_date(
        event_id: int, 
        date_id: int, 
        user: User, 
        availability: str
    ) -> DateVote:
        """
        Vote on availability for a proposed date.
        User must be invited to the event (or be the owner).
        
        Args:
            event_id: ID of the event.
            date_id: ID of the proposed date.
            user: User voting.
            availability: Availability choice (AVAILABLE, MAYBE, NOT_AVAILABLE).
        
        Returns:
            DateVote instance (created or updated).
            
        Raises:
            NotFoundError: If event or proposed date not found.
            ValidationError: If event is cancelled or confirmed.
        """
        event = EventService.get_event_by_id(event_id, user)
        
        if not event:
            raise NotFoundError("Event not found or you don't have access")
        
        if event.status == Event.Status.CANCELLED:
            raise ValidationError("Cannot vote on a cancelled event")
        
        if event.status == Event.Status.CONFIRMED:
            raise ValidationError("Cannot vote on a confirmed event")
        
        # Check if proposed date exists and belongs to event
        try:
            proposed_date = ProposedDate.objects.get(id=date_id, event=event)
        except ProposedDate.DoesNotExist:
            raise NotFoundError("Proposed date not found")
        
        # Create or update vote
        vote, created = DateVote.objects.update_or_create(
            proposed_date=proposed_date,
            user=user,
            defaults={'availability': availability}
        )
        
        return vote
    
    @staticmethod
    def get_event_votes(event_id: int, user: User) -> List[Dict]:
        """
        Get all votes for an event.
        User must be owner or invitee to view votes.
        
        Args:
            event_id: ID of the event.
            user: User requesting votes.
        
        Returns:
            List of dicts with vote data for each proposed date.
            
        Raises:
            NotFoundError: If event not found or user has no access.
        """
        event = EventService.get_event_by_id(event_id, user)
        
        if not event:
            raise NotFoundError("Event not found or you don't have access")
        
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
        
        return result
    
    @staticmethod
    def get_user_votes_for_event(event_id: int, user: User) -> QuerySet[DateVote]:
        """
        Get the current user's votes for an event.
        
        Args:
            event_id: ID of the event.
            user: User whose votes to retrieve.
        
        Returns:
            QuerySet of DateVote instances.
            
        Raises:
            NotFoundError: If event not found or user has no access.
        """
        event = EventService.get_event_by_id(event_id, user)
        
        if not event:
            raise NotFoundError("Event not found or you don't have access")
        
        # Get user's votes for this event
        return DateVote.objects.filter(
            proposed_date__event=event,
            user=user
        ).select_related('proposed_date')
    
    @staticmethod
    def delete_vote(event_id: int, date_id: int, user: User) -> Dict:
        """
        Delete a user's vote for a proposed date.
        
        Args:
            event_id: ID of the event.
            date_id: ID of the proposed date.
            user: User whose vote to delete.
        
        Returns:
            Dict with success message.
            
        Raises:
            NotFoundError: If event, proposed date, or vote not found.
            ValidationError: If event is cancelled or confirmed.
        """
        event = EventService.get_event_by_id(event_id, user)
        
        if not event:
            raise NotFoundError("Event not found or you don't have access")
        
        if event.status == Event.Status.CANCELLED:
            raise ValidationError("Cannot modify votes on a cancelled event")
        
        if event.status == Event.Status.CONFIRMED:
            raise ValidationError("Cannot modify votes on a confirmed event")
        
        # Check if proposed date exists
        try:
            proposed_date = ProposedDate.objects.get(id=date_id, event=event)
        except ProposedDate.DoesNotExist:
            raise NotFoundError("Proposed date not found")
        
        # Delete the vote
        try:
            vote = DateVote.objects.get(proposed_date=proposed_date, user=user)
            vote.delete()
            return {"message": "Vote deleted successfully"}
        except DateVote.DoesNotExist:
            raise NotFoundError("Vote not found")
