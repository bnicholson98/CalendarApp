"""
Event-related views for calendar event management.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.serializers import EventSerializer, BulkEventCreateSerializer
from core.services.event_service import EventService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):
    """
    Create calendar event
    
    Args:
        request: HTTP request containing event_name, dates array.
                User must be authenticated.
    
    Returns:
        Response with success message or error.
    """
    # Use the serializer for validation
    serializer = BulkEventCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        # Check if we need to maintain backward compatibility for empty dates error message
        errors = serializer.errors
        if 'dates' in errors or 'event_name' in errors:
            return Response(
                {"error": "Event name and dates are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    event_name = validated_data['event_name']
    dates = validated_data['dates']
    
    try:
        # Use the service layer for business logic
        success, response_data = EventService.create_events(
            event_name=event_name,
            dates=dates,
            user=request.user
        )
        
        if success:
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    except ValueError as e:
        # Re-raise ValueError to maintain test compatibility
        raise


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_events(request):
    """
    List all events for the authenticated user.
    
    Args:
        request: HTTP request from an authenticated user.
    
    Returns:
        Response with serialized list of user's events.
    """
    # Use the service layer to get events
    events = EventService.get_user_events(request.user)
    
    # Serialize the events
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
    # Use the service layer to get the event
    event = EventService.get_user_event_by_id(event_id, request.user)
    
    if not event:
        return Response(
            {"error": "Event not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Use the standard serializer for single event
    serializer = EventSerializer(event)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_event(request, event_id):
    """
    Update an existing event.
    
    Args:
        request: HTTP request containing updated event data.
        event_id: ID of the event to update.
    
    Returns:
        Response with updated event data or error.
    """
    # Use the service layer to update the event
    success, result = EventService.update_event(
        event_id=event_id,
        user=request.user,
        data=request.data
    )
    
    if success:
        # result is the serializer instance
        return Response(result.data, status=status.HTTP_200_OK)
    else:
        if isinstance(result, dict) and 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        else:
            # result is the serializer with errors
            return Response(result.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_event(request, event_id):
    """
    Delete a specific event.
    
    Args:
        request: HTTP request from an authenticated user.
        event_id: ID of the event to delete.
    
    Returns:
        Response with success message or error.
    """
    # Use the service layer to delete the event
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
