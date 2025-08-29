"""
Service layer for event-related business logic.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from core.models import Event
from core.serializers import EventSerializer


class EventService:
    """Service class for handling event business logic."""
    
    @staticmethod
    def create_events(event_name: str, dates: List[datetime], user: User) -> Tuple[bool, Dict]:
        """
        Create calendar events for multiple dates.
        
        Args:
            event_name: Name of the event.
            dates: List of date strings in 'YYYY-MM-DD' format.
            user: User creating the events.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """        
        try:
            event_instances = []
            
            # Create event instances
            for date in dates:
                event = Event(
                    event_name=event_name, 
                    user=user, 
                    date=date
                )
                event_instances.append(event)
            
            # Bulk create all events
            with transaction.atomic():
                Event.objects.bulk_create(event_instances)
            
            return True, {"success": "Event created"}
        
        except ValueError as e:
            raise  
        except Exception as e:
            return False, {"error": f"Failed to create events: {str(e)}"}
    
    @staticmethod
    def get_user_events(user: User) -> List[Event]:
        """
        Get all events for a specific user.
        
        Args:
            user: User whose events to retrieve.
        
        Returns:
            QuerySet of events ordered by date.
        """
        return Event.objects.filter(user=user).order_by('date')
    
    @staticmethod
    def get_user_event_by_id(event_id: int, user: User) -> Optional[Event]:
        """
        Get a specific event by ID for a user.
        
        Args:
            event_id: ID of the event.
            user: User who owns the event.
        
        Returns:
            Event instance or None if not found.
        """
        try:
            return Event.objects.get(id=event_id, user=user)
        except Event.DoesNotExist:
            return None
    
    @staticmethod
    def update_event(event_id: int, user: User, data: Dict) -> Tuple[bool, Dict]:
        """
        Update an existing event.
        
        Args:
            event_id: ID of the event to update.
            user: User who owns the event.
            data: Dictionary containing update data.
        
        Returns:
            Tuple of (success: bool, response_data: dict or serializer)
        """
        event = EventService.get_user_event_by_id(event_id, user)
        
        if not event:
            return False, {"error": "Event not found"}
        
        # Create serializer context with request
        context = {'request': type('obj', (object,), {'user': user})}
        serializer = EventSerializer(event, data=data, partial=True, context=context)
        
        if serializer.is_valid():
            serializer.save()
            return True, serializer
        
        return False, serializer
    
    @staticmethod
    def delete_event(event_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Delete a specific event.
        
        Args:
            event_id: ID of the event to delete.
            user: User who owns the event.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        event = EventService.get_user_event_by_id(event_id, user)
        
        if not event:
            return False, {"error": "Event not found"}
        
        try:
            event.delete()
            return True, {"message": "Event deleted successfully"}
        except Exception as e:
            return False, {"error": f"Failed to delete event: {str(e)}"}
