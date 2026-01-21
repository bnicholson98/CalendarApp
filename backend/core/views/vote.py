"""
Vote-related views for date availability voting.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.serializers import VoteCreateSerializer, DateVoteSerializer
from core.services.vote_service import VoteService
from core.exceptions import NotFoundError, ValidationError


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
    serializer = VoteCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:
        vote = VoteService.vote_on_date(
            event_id=event_id,
            date_id=date_id,
            user=request.user,
            availability=validated_data['availability']
        )
        output_serializer = DateVoteSerializer(vote)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)


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
    try:
        result = VoteService.get_event_votes(event_id=event_id, user=request.user)
        return Response(result, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)


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
    try:
        votes = VoteService.get_user_votes_for_event(event_id=event_id, user=request.user)
        serializer = DateVoteSerializer(votes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)


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
    try:
        VoteService.delete_vote(event_id=event_id, date_id=date_id, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
