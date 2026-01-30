"""
Service layer for event invite-related business logic.
"""
from typing import List, Optional, Dict
from django.contrib.auth.models import User
from django.db.models import QuerySet

from core.models import Event, EventInvite
from core.exceptions import NotFoundError, ValidationError, PermissionDeniedError


class EventInviteService:
    """Service class for handling event invite business logic."""
    
    @staticmethod
    def create_invite(event_id: int, invitee_id: int, user: User) -> EventInvite:
        """
        Create an event invite.
        
        Args:
            event_id: ID of the event.
            invitee_id: ID of the user to invite.
            user: User creating the invite (must be event owner).
        
        Returns:
            Created EventInvite instance.
            
        Raises:
            NotFoundError: If event not found.
        """
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise NotFoundError("Event not found")
        
        invite = EventInvite.objects.create(
            event_id=event_id,
            owner=user,
            invitee_id=invitee_id,
            status=EventInvite.Status.PENDING
        )
        
        return invite
    
    @staticmethod
    def get_user_received_invites(user: User) -> QuerySet[EventInvite]:
        """
        Get all invites received by a user.
        
        Args:
            user: User whose received invites to retrieve.
        
        Returns:
            QuerySet of invites ordered by created_at descending.
        """
        return EventInvite.objects.filter(
            invitee=user
        ).exclude(
            event__status=Event.Status.CANCELLED
        ).select_related('invitee').order_by('-created_at')
    
    @staticmethod
    def get_user_sent_invites(user: User) -> QuerySet[EventInvite]:
        """
        Get all invites sent by a user.
        
        Args:
            user: User whose sent invites to retrieve.
        
        Returns:
            QuerySet of invites ordered by created_at descending.
        """
        return EventInvite.objects.filter(owner=user).select_related('invitee').order_by('-created_at')
    
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

        Raises:
            NotFoundError: If invite not found.
        """
        try:
            return EventInvite.objects.get(id=invite_id)
        except EventInvite.DoesNotExist:
            raise NotFoundError("Event invite not found")
    
    @staticmethod
    def update_invite_status(invite_id: int, user: User, new_status: str) -> EventInvite:
        """
        Update the status of an invite.
        Only the invitee can update the status.
        
        Args:
            invite_id: ID of the invite to update.
            user: User updating the invite (must be invitee).
            new_status: New status value.
        
        Returns:
            Updated EventInvite instance.
            
        Raises:
            NotFoundError: If invite not found.
            PermissionDeniedError: If user is not the invitee.
        """
        try:
            invite = EventInvite.objects.get(id=invite_id)
        except EventInvite.DoesNotExist:
            raise NotFoundError("Invite not found")
        
        # Only invitee can update status
        if invite.invitee != user:
            raise PermissionDeniedError("Only the invitee can update the invite status")
        
        invite.status = new_status
        invite.save()
        
        return invite
    
    @staticmethod
    def get_event_invites(event_id: int, user: User) -> QuerySet[EventInvite]:
        """
        Get all invites for a specific event.
        Only the event owner can view the full invitee list.
        
        Args:
            event_id: ID of the event.
            user: User requesting the invites (must be event owner).
        
        Returns:
            QuerySet of invites ordered by created_at descending.
            
        Raises:
            NotFoundError: If event not found or user is not the owner.
        """
        try:
            Event.objects.get(id=event_id, user=user)
        except Event.DoesNotExist:
            raise NotFoundError("Event not found or you are not the owner")
        
        return EventInvite.objects.filter(
            event_id=event_id
        ).select_related('invitee').order_by('-created_at')
    
    @staticmethod
    def delete_invite(invite_id: int, user: User) -> Dict:
        """
        Delete a specific invite.
        Only the owner can delete an invite.
        
        Args:
            invite_id: ID of the invite to delete.
            user: User who owns the invite.
        
        Returns:
            Dict with success message.
            
        Raises:
            NotFoundError: If invite not found.
            PermissionDeniedError: If user is not the owner.
        """
        try:
            invite = EventInvite.objects.get(id=invite_id)
        except EventInvite.DoesNotExist:
            raise NotFoundError("Invite not found")
        
        # Only owner can delete invite
        if invite.owner != user:
            raise PermissionDeniedError("Only the invite owner can delete the invite")
        
        invite.delete()
        return {"message": "Invite deleted successfully"}
