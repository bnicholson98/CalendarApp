from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import make_password
from .models import Event
from .serializers import EventSerializer

@api_view(["POST"])
def register_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password)
    return JsonResponse({"message": "User created successfully"}, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return JsonResponse(
            {
                "token": token.key,
                "userName": username
            }, status=status.HTTP_200_OK)
    
    return JsonResponse({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def logout_user(request):
    token = request.auth

    if token:
        token.delete()
        return JsonResponse({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    
    return JsonResponse({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):
    event_name = request.data.get('event_name')
    dates = request.data.get('dates')

    if not event_name or not dates:
        return Response({"error": "Event name and dates are required"}, status=status.HTTP_400_BAD_REQUEST)

    event_instances = []
    for date_str in dates:
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        event = Event(event_name=event_name, user=request.user, date=date)
        print(event)
        event_instances.append(event)

    Event.objects.bulk_create(event_instances)
    
    return Response({"success": "Event created"}, status=status.HTTP_201_CREATED)