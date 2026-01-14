"""
Vote-related views for date availability voting.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.services.vote_service import VoteService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_on_date(request, event_id, date_id):
    """
    Vote on availability for a proposed date.
    User must be invited to the event (or be the owner).
    
    Args:
        request: HTTP request containing availability.
        event_id: ID of the event.
        date_id: ID of the proposed date.
    
    Returns:
        Response with vote data or error.
    """
    availability = request.data.get('availability')
    
    if not availability:
        return Response(
            {"error": "Availability is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    success, result = VoteService.vote_on_date(
        event_id=event_id,
        date_id=date_id,
        user=request.user,
        availability=availability
    )
    
    if success:
        return Response(result, status=status.HTTP_200_OK)
    else:
        error = result.get('error', '')
        if error == "Event not found or you don't have access":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        if error == "Proposed date not found":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_event_votes(request, event_id):
    """
    Get all votes for an event.
    User must be owner or invitee to view votes.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event.
    
    Returns:
        Response with all votes for each proposed date or error.
    """
    success, result = VoteService.get_event_votes(
        event_id=event_id,
        user=request.user
    )
    
    if success:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_votes(request, event_id):
    """
    Get the current user's votes for an event.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event.
    
    Returns:
        Response with user's votes or error.
    """
    success, result = VoteService.get_user_votes_for_event(
        event_id=event_id,
        user=request.user
    )
    
    if success:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_vote(request, event_id, date_id):
    """
    Delete a user's vote for a proposed date.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event.
        date_id: ID of the proposed date.
    
    Returns:
        Response with success message or error.
    """
    success, result = VoteService.delete_vote(
        event_id=event_id,
        date_id=date_id,
        user=request.user
    )
    
    if success:
        return Response(result, status=status.HTTP_204_NO_CONTENT)
    else:
        error = result.get('error', '')
        if error == "Event not found or you don't have access":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        if error == "Proposed date not found":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        if error == "Vote not found":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
