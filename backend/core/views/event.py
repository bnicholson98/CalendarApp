"""
Event-related views for calendar event management.
"""
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.serializers import EventSerializer, EventCreateSerializer, EventConfirmSerializer, ProposedDateCreateSerializer
from core.services.event_service import EventService


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
        errors = serializer.errors
        if 'proposed_dates' in errors or 'event_name' in errors:
            return Response(
                {"error": "Event name and proposed dates are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    success, response_data = EventService.create_event_proposal(
        event_name=validated_data['event_name'],
        proposed_dates=validated_data['proposed_dates'],
        user=request.user,
        invitees=validated_data.get('invitees', [])
    )
    
    if success:
        return Response(response_data, status=status.HTTP_201_CREATED)
    else:
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


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
    success, result = EventService.update_event(
        event_id=event_id,
        user=request.user,
        data=request.data
    )
    
    if success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        if isinstance(result, dict) and 'error' in result:
            if result['error'] == "Event not found":
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result.errors, status=status.HTTP_400_BAD_REQUEST)


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
    success, response_data = EventService.delete_event(
        event_id=event_id,
        user=request.user
    )
    
    if success:
        return Response(
            response_data, 
            status=status.HTTP_204_NO_CONTENT
        )
    else:
        return Response(
            response_data, 
            status=status.HTTP_404_NOT_FOUND
        )


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
    # First check if event exists
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
    
    success, result = EventService.confirm_event(
        event_id=event_id,
        user=request.user,
        proposed_date_id=serializer.validated_data['proposed_date_id']
    )
    
    if success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


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
    success, result = EventService.cancel_event(
        event_id=event_id,
        user=request.user
    )
    
    if success:
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        if result.get('error') == "Event not found":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


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
    success, result = EventService.get_proposed_dates(
        event_id=event_id,
        user=request.user
    )
    
    if success:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_404_NOT_FOUND)


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
        errors = serializer.errors
        if 'date' in errors:
            return Response(
                {"error": "Date is required in YYYY-MM-DD format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    success, result = EventService.add_proposed_date(
        event_id=event_id,
        date_value=validated_data['date'],
        user=request.user
    )
    
    if success:
        return Response(result, status=status.HTTP_201_CREATED)
    else:
        if result.get('error') == "Event not found or you are not the owner":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


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
    success, result = EventService.remove_proposed_date(
        event_id=event_id,
        date_id=date_id,
        user=request.user
    )
    
    if success:
        return Response(result, status=status.HTTP_204_NO_CONTENT)
    else:
        error = result.get('error', '')
        if error == "Event not found or you are not the owner":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        if error == "Proposed date not found":
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
