"""
Service layer for event invite-related business logic.
"""
from typing import List, Dict, Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from core.models import Event, EventInvite
from core.serializers import EventInviteSerializer


class EventInviteService:
    """Service class for handling event invite business logic."""
    
    @staticmethod
    def create_invite(event_id: int, invitee_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Create an event invite.
        
        Args:
            event_id: ID of the event.
            invitee_id: ID of the user to invite.
            user: User creating the invite (must be event owner).
        
        Returns:
            Tuple of (success: bool, response_data: dict or serializer)
        """
        data = {
            'event': event_id,
            'invitee': invitee_id,
        }
        
        context = {'request': type('obj', (object,), {'user': user})}
        serializer = EventInviteSerializer(data=data, context=context)
        
        if serializer.is_valid():
            serializer.save()
            return True, serializer
        
        return False, serializer
    
    @staticmethod
    def get_user_received_invites(user: User) -> List[EventInvite]:
        """
        Get all invites received by a user.
        
        Args:
            user: User whose received invites to retrieve.
        
        Returns:
            QuerySet of invites ordered by created_at descending.
        """
        return EventInvite.objects.filter(invitee=user).order_by('-created_at')
    
    @staticmethod
    def get_user_sent_invites(user: User) -> List[EventInvite]:
        """
        Get all invites sent by a user.
        
        Args:
            user: User whose sent invites to retrieve.
        
        Returns:
            QuerySet of invites ordered by created_at descending.
        """
        return EventInvite.objects.filter(owner=user).order_by('-created_at')
    
    @staticmethod
    def get_invite_by_id(invite_id: int, user: User) -> Optional[EventInvite]:
        """
        Get a specific invite by ID for a user.
        User must be either the owner or the invitee.
        
        Args:
            invite_id: ID of the invite.
            user: User requesting the invite.
        
        Returns:
            EventInvite instance or None if not found.
        """
        try:
            return EventInvite.objects.get(
                id=invite_id,
            )
        except EventInvite.DoesNotExist:
            return None
    
    @staticmethod
    def update_invite_status(invite_id: int, user: User, status: str) -> Tuple[bool, Dict]:
        """
        Update the status of an invite.
        Only the invitee can update the status.
        
        Args:
            invite_id: ID of the invite to update.
            user: User updating the invite (must be invitee).
            status: New status value.
        
        Returns:
            Tuple of (success: bool, response_data: dict or serializer)
        """
        try:
            invite = EventInvite.objects.get(id=invite_id)
        except EventInvite.DoesNotExist:
            return False, {"error": "Invite not found"}
        
        # Only invitee can update status
        if invite.invitee != user:
            return False, {"error": "Only the invitee can update the invite status"}
        
        # Validate status
        valid_statuses = [choice[0] for choice in EventInvite.Status.choices]
        if status not in valid_statuses:
            return False, {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
        
        invite.status = status
        invite.save()
        
        context = {'request': type('obj', (object,), {'user': user})}
        serializer = EventInviteSerializer(invite, context=context)
        return True, serializer
    
    @staticmethod
    def delete_invite(invite_id: int, user: User) -> Tuple[bool, Dict]:
        """
        Delete a specific invite.
        Only the owner can delete an invite.
        
        Args:
            invite_id: ID of the invite to delete.
            user: User who owns the invite.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        try:
            invite = EventInvite.objects.get(id=invite_id)
        except EventInvite.DoesNotExist:
            return False, {"error": "Invite not found"}
        
        # Only owner can delete invite
        if invite.owner != user:
            return False, {"error": "Only the invite owner can delete the invite"}
        
        try:
            invite.delete()
            return True, {"message": "Invite deleted successfully"}
        except Exception as e:
            return False, {"error": f"Failed to delete invite: {str(e)}"}
