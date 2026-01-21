"""
Event invite-related views for calendar event invitation management.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.serializers import EventInviteSerializer, InviteStatusUpdateSerializer
from core.services.event_invite_service import EventInviteService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_invite(request):
    """
    Create an event invite.
    
    Args:
        request: HTTP request containing event and invitee IDs.
                User must be authenticated and be the event owner.
    
    Returns:
        Response with created invite data or error.
    """
    serializer = EventInviteSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        errors = serializer.errors
        if 'event' in errors or 'invitee' in errors:
            return Response(
                {"error": "Event and invitee are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    success, result = EventInviteService.create_invite(
        event_id=serializer.validated_data['event'].id,
        invitee_id=serializer.validated_data['invitee'].id,
        user=request.user
    )
    
    if success:
        return Response(result.data, status=status.HTTP_201_CREATED)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_received_invites(request):
    """
    List all invites received by the authenticated user.
    
    Args:
        request: HTTP request from an authenticated user.
    
    Returns:
        Response with serialized list of received invites.
    """
    invites = EventInviteService.get_user_received_invites(request.user)
    serializer = EventInviteSerializer(invites, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sent_invites(request):
    """
    List all invites sent by the authenticated user.
    
    Args:
        request: HTTP request from an authenticated user.
    
    Returns:
        Response with serialized list of sent invites.
    """
    invites = EventInviteService.get_user_sent_invites(request.user)
    serializer = EventInviteSerializer(invites, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invite(request, invite_id):
    """
    Retrieve a specific invite by ID.
    
    Args:
        request: HTTP request from an authenticated user.
        invite_id: ID of the invite to retrieve.
    
    Returns:
        Response with serialized invite data or error.
    """
    invite = EventInviteService.get_invite_by_id(invite_id, request.user)
    
    if not invite:
        return Response(
            {"error": "Invite not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = EventInviteSerializer(invite)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_invite_status(request, invite_id):
    """
    Update the status of an invite.
    Only the invitee can update the status.
    
    Args:
        request: HTTP request containing the new status.
        invite_id: ID of the invite to update.
    
    Returns:
        Response with updated invite data or error.
    """
    serializer = InviteStatusUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        errors = serializer.errors
        if 'status' in errors:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    success, result = EventInviteService.update_invite_status(
        invite_id=invite_id,
        user=request.user,
        new_status=validated_data['status']
    )
    
    if success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        if result.get('error') == "Invite not found":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        elif result.get('error') == "Only the invitee can update the invite status":
            return Response(result, status=status.HTTP_403_FORBIDDEN)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_invite(request, invite_id):
    """
    Delete a specific invite.
    Only the owner can delete an invite.
    
    Args:
        request: HTTP request from an authenticated user.
        invite_id: ID of the invite to delete.
    
    Returns:
        Response with success message or error.
    """
    success, response_data = EventInviteService.delete_invite(
        invite_id=invite_id,
        user=request.user
    )
    
    if success:
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)
    else:
        if response_data.get('error') == "Invite not found":
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        elif response_data.get('error') == "Only the invite owner can delete the invite":
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
