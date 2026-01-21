"""
Event-related views for calendar event management.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.serializers import (
    EventSerializer,
    EventCreateSerializer,
    EventConfirmSerializer,
    EventUpdateSerializer,
    ProposedDateSerializer,
    ProposedDateCreateSerializer,
)
from core.services.event_service import EventService
from core.exceptions import NotFoundError, ValidationError


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):
    """
    Create an event proposal with multiple proposed dates and optional invitees.
    
    Args:
        request: HTTP request containing event_name, proposed_dates array, and optional invitees array.
                User must be authenticated.
    
    Returns:
        Response with success message and event_id or error.
    """
    serializer = EventCreateSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:
        response_data = EventService.create_event_proposal(
            event_name=validated_data['event_name'],
            proposed_dates=validated_data['proposed_dates'],
            user=request.user,
            invitees=validated_data.get('invitees', [])
        )
        return Response(response_data, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_events(request):
    """
    List all events for the authenticated user (owned or invited to).
    
    Args:
        request: HTTP request from an authenticated user.
    
    Returns:
        Response with serialized list of user's events.
    """
    events = EventService.get_user_events(request.user)
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_event(request, event_id):
    """
    Retrieve a specific event by ID.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event to retrieve.
    
    Returns:
        Response with serialized event data or error.
    """
    event = EventService.get_event_by_id(event_id, request.user)
    
    if not event:
        return Response(
            {"error": "Event not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = EventSerializer(event)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_event(request, event_id):
    """
    Update an existing event (only event_name can be updated).
    Only the owner can update.
    
    Args:
        request: HTTP request containing updated event data.
        event_id: ID of the event to update.
    
    Returns:
        Response with updated event data or error.
    """
    serializer = EventUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:      
        response_data = EventService.update_event(
            event_id=event_id,
            user=request.user,
            event_name=validated_data.get('event_name')
        )
        output_serializer = EventSerializer(response_data)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_event(request, event_id):
    """
    Delete a specific event.
    Only the owner can delete.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event to delete.
    
    Returns:
        Response with success message or error.
    """
    try:
        EventService.delete_event(event_id=event_id, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_event(request, event_id):
    """
    Confirm an event with a specific proposed date.
    Only the owner can confirm.
    
    Args:
        request: HTTP request containing proposed_date_id.
        event_id: ID of the event to confirm.
    
    Returns:
        Response with updated event data or error.
    """
    # First check if event exists and user is owner
    event = EventService.get_event_by_id_owner_only(event_id, request.user)
    if not event:
        return Response(
            {"error": "Event not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = EventConfirmSerializer(
        data=request.data, 
        context={'request': request, 'event': event}
    )

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:
        response_data = EventService.confirm_event(
            event=event,
            user=request.user,
            proposed_date_id=validated_data['proposed_date_id']
        )
        output_serializer = EventSerializer(response_data)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_event(request, event_id):
    """
    Cancel an event.
    Only the owner can cancel.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event to cancel.
    
    Returns:
        Response with updated event data or error.
    """
    try:
        event = EventService.cancel_event(event_id=event_id, user=request.user)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_proposed_dates(request, event_id):
    """
    List all proposed dates for an event.
    User must be owner or invitee.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event.
    
    Returns:
        Response with list of proposed dates or error.
    """
    try:
        proposed_dates = EventService.get_proposed_dates(event_id=event_id, user=request.user)
        serializer = ProposedDateSerializer(proposed_dates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_proposed_date(request, event_id):
    """
    Add a proposed date to an event.
    Only the event owner can add proposed dates.
    
    Args:
        request: HTTP request containing date.
        event_id: ID of the event.
    
    Returns:
        Response with created proposed date data or error.
    """
    serializer = ProposedDateCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:
        proposed_date = EventService.add_proposed_date(
            event_id=event_id,
            date_value=validated_data['date'],
            user=request.user
        )
        output_serializer = ProposedDateSerializer(proposed_date)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_proposed_date(request, event_id, date_id):
    """
    Remove a proposed date from an event.
    Only the event owner can remove proposed dates.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event.
        date_id: ID of the proposed date to remove.
    
    Returns:
        Response with success message or error.
    """
    try:
        EventService.remove_proposed_date(
            event_id=event_id,
            date_id=date_id,
            user=request.user
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
    except NotFoundError as e:
        return Response({"error": e.message}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
