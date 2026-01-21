"""
Service layer for event-related business logic.
"""
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from core.models import Event, EventInvite, ProposedDate


class EventService:
    """Service class for handling event business logic."""
    
    @staticmethod
    def _get_accessible_events_filter(user: User) -> Q:
        """
        Get the Q filter for events accessible to a user (owned or invited).
        
        Args:
            user: User to check access for.
        
        Returns:
            Q object filter for accessible events.
        """
        return Q(user=user) | Q(invites__invitee=user)
    
    @staticmethod
    def create_event_proposal(
        event_name: str, 
        proposed_dates: List[datetime], 
        user: User,
        invitees: List[int] = None
    ) -> Tuple[bool, Dict]:
        """
        Create an event proposal with multiple proposed dates and optional invitees.
        
        Args:
            event_name: Name of the event.
            proposed_dates: List of dates for the proposal.
            user: User creating the event.
            invitees: Optional list of user IDs to invite.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            with transaction.atomic():
                # Create the event
                event = Event.objects.create(
                    event_name=event_name,
                    user=user,
                    status=Event.Status.PROPOSED
                )
                
                # Create proposed dates
                proposed_date_instances = []
                for date_val in proposed_dates:
                    proposed_date = ProposedDate(
                        event=event,
                        date=date_val
                    )
                    proposed_date_instances.append(proposed_date)
                
                ProposedDate.objects.bulk_create(proposed_date_instances)
                
                # Create invites if invitees provided
                if invitees:
                    invite_instances = []
                    for invitee_id in invitees:
                        invite = EventInvite(
                            event=event,
                            owner=user,
                            invitee_id=invitee_id,
                            status=EventInvite.Status.PENDING
                        )
                        invite_instances.append(invite)
                    
                    EventInvite.objects.bulk_create(invite_instances)
                
                return True, {"event_id": event.id, "message": "Event proposal created successfully"}
        
        except Exception as e:
            return False, {"error": f"Failed to create event proposal: {str(e)}"}
    
    @staticmethod
    def get_user_events(user: User) -> List[Event]:
        """
        Get all events for a specific user (owned or invited to).
        
        Args:
            user: User whose events to retrieve.
        
        Returns:
            QuerySet of events.
        """
        return Event.objects.filter(
            EventService._get_accessible_events_filter(user)
        ).distinct().order_by('-created_at')
    
    @staticmethod
    def get_user_owned_events(user: User) -> List[Event]:
        """
        Get all events owned by a specific user.
        
        Args:
            user: User whose owned events to retrieve.
        
        Returns:
            QuerySet of events.
        """
        return Event.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_event_by_id(event_id: int, user: User) -> Optional[Event]:
        """
        Get a specific event by ID for a user (must be owner or invitee).
        
        Args:
            event_id: ID of the event.
            user: User requesting the event.
        
        Returns:
            Event instance or None if not found or not authorized.
        """
        try:
            return Event.objects.filter(
                EventService._get_accessible_events_filter(user)
            ).distinct().get(id=event_id)
        except Event.DoesNotExist:
            return None
    
    @staticmethod
    def get_event_by_id_owner_only(event_id: int, user: User) -> Optional[Event]:
        """
        Get a specific event by ID only if user is the owner.
        
        Args:
            event_id: ID of the event.
            user: User who should be the owner.
        
        Returns:
            Event instance or None if not found or not owner.
        """
        try:
            return Event.objects.get(id=event_id, user=user)
        except Event.DoesNotExist:
            return None
    
    @staticmethod
    def update_event(event_id: int, user: User, data: Dict) -> Tuple[bool, Dict]:
        """
        Update an existing event (only event_name can be updated).
        Only the owner can update.
        
        Args:
            event_id: ID of the event to update.
            user: User who owns the event.
            data: Dictionary containing update data.
        
        Returns:
            Tuple of (success: bool, response_data: dict or serializer)
        """
        event = EventService.get_event_by_id_owner_only(event_id, user)
        
        if not event:
            return False, {"error": "Event not found"}
        
        # Only allow updating event_name
        if 'event_name' in data:
            event_name = data['event_name']
            if not event_name or not event_name.strip():
                return False, {"error": "Event name cannot be empty"}
            event.event_name = event_name.strip()
            event.save()
        
        from core.serializers import EventSerializer
        context = {'request': type('obj', (object,), {'user': user})}
        serializer = EventSerializer(event, context=context)
        return True, serializer
    
    @staticmethod
    def delete_event(event_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Delete a specific event.
        Only the owner can delete.
        
        Args:
            event_id: ID of the event to delete.
            user: User who owns the event.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        event = EventService.get_event_by_id_owner_only(event_id, user)
        
        if not event:
            return False, {"error": "Event not found"}
        
        try:
            event.delete()
            return True, {"message": "Event deleted successfully"}
        except Exception as e:
            return False, {"error": f"Failed to delete event: {str(e)}"}
    
    @staticmethod
    def confirm_event(event_id: int, user: User, proposed_date_id: int) -> Tuple[bool, Dict]:
        """
        Confirm an event with a specific proposed date.
        Only the owner can confirm.
        
        Args:
            event_id: ID of the event to confirm.
            user: User who owns the event.
            proposed_date_id: ID of the proposed date to confirm.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        event = EventService.get_event_by_id_owner_only(event_id, user)
        
        if not event:
            return False, {"error": "Event not found"}
        
        if event.status == Event.Status.CONFIRMED:
            return False, {"error": "Event is already confirmed"}
        
        if event.status == Event.Status.CANCELLED:
            return False, {"error": "Cannot confirm a cancelled event"}
        
        try:
            proposed_date = ProposedDate.objects.get(id=proposed_date_id, event=event)
        except ProposedDate.DoesNotExist:
            return False, {"error": "Proposed date not found or does not belong to this event"}
        
        event.status = Event.Status.CONFIRMED
        event.confirmed_date = proposed_date
        event.save()
        
        from core.serializers import EventSerializer
        context = {'request': type('obj', (object,), {'user': user})}
        serializer = EventSerializer(event, context=context)
        return True, serializer
    
    @staticmethod
    def cancel_event(event_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Cancel an event.
        Only the owner can cancel.
        
        Args:
            event_id: ID of the event to cancel.
            user: User who owns the event.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        event = EventService.get_event_by_id_owner_only(event_id, user)
        
        if not event:
            return False, {"error": "Event not found"}
        
        if event.status == Event.Status.CANCELLED:
            return False, {"error": "Event is already cancelled"}
        
        event.status = Event.Status.CANCELLED
        event.save()
        
        from core.serializers import EventSerializer
        context = {'request': type('obj', (object,), {'user': user})}
        serializer = EventSerializer(event, context=context)
        return True, serializer
    
    @staticmethod
    def add_proposed_date(event_id: int, date_value: date, user: User) -> Tuple[bool, Dict]:
        """
        Add a proposed date to an event.
        Only the event owner can add proposed dates.
        
        Args:
            event_id: ID of the event.
            date_value: Date to add.
            user: User making the request (must be event owner).
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        event = EventService.get_event_by_id_owner_only(event_id, user)
        
        if not event:
            return False, {"error": "Event not found or you are not the owner"}
        
        if event.status == Event.Status.CONFIRMED:
            return False, {"error": "Cannot add dates to a confirmed event"}
        
        if event.status == Event.Status.CANCELLED:
            return False, {"error": "Cannot add dates to a cancelled event"}
        
        # Check if date already exists for this event
        if ProposedDate.objects.filter(event=event, date=date_value).exists():
            return False, {"error": "This date has already been proposed for this event"}
        
        try:
            proposed_date = ProposedDate.objects.create(
                event=event,
                date=date_value
            )
            
            from core.serializers import ProposedDateSerializer
            serializer = ProposedDateSerializer(proposed_date)
            return True, serializer.data
        
        except Exception as e:
            return False, {"error": f"Failed to add proposed date: {str(e)}"}
    
    @staticmethod
    def remove_proposed_date(event_id: int, date_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Remove a proposed date from an event.
        Only the event owner can remove proposed dates.
        Cannot remove the last proposed date.
        Cannot remove the confirmed date.
        
        Args:
            event_id: ID of the event.
            date_id: ID of the proposed date to remove.
            user: User making the request (must be event owner).
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        event = EventService.get_event_by_id_owner_only(event_id, user)
        
        if not event:
            return False, {"error": "Event not found or you are not the owner"}
        
        if event.status == Event.Status.CANCELLED:
            return False, {"error": "Cannot modify a cancelled event"}
        
        try:
            proposed_date = ProposedDate.objects.get(id=date_id, event=event)
        except ProposedDate.DoesNotExist:
            return False, {"error": "Proposed date not found"}
        
        # Cannot remove the confirmed date
        if event.confirmed_date and event.confirmed_date.id == date_id:
            return False, {"error": "Cannot remove the confirmed date"}
        
        # Cannot remove the last proposed date
        if event.proposed_dates.count() <= 1:
            return False, {"error": "Cannot remove the last proposed date"}
        
        try:
            proposed_date.delete()
            return True, {"message": "Proposed date removed successfully"}
        except Exception as e:
            return False, {"error": f"Failed to remove proposed date: {str(e)}"}
    
    @staticmethod
    def get_proposed_dates(event_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Get all proposed dates for an event.
        User must be owner or invitee.
        
        Args:
            event_id: ID of the event.
            user: User making the request.
        
        Returns:
            Tuple of (success: bool, response_data: dict or list)
        """
        event = EventService.get_event_by_id(event_id, user)
        
        if not event:
            return False, {"error": "Event not found"}
        
        proposed_dates = event.proposed_dates.all()
        
        from core.serializers import ProposedDateSerializer
        serializer = ProposedDateSerializer(proposed_dates, many=True)
        return True, serializer.data
