"""
Authentication-related views for user registration, login, and logout.
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from core.serializers import UserRegistrationSerializer, LoginSerializer
from core.services.auth_service import AuthService


@api_view(["POST"])
def register_user(request):
    """
    Register a new user.
    
    Args:
        request: HTTP request containing username and password in data.
    
    Returns:
        JsonResponse with success message or error.
    """
    # Use serializer for validation
    serializer = UserRegistrationSerializer(data=request.data)
    
    # Check if data is valid
    if not serializer.is_valid():
        # Maintain backward compatibility with original error messages
        errors = serializer.errors
        if 'username' in errors or 'password' in errors:
            return Response(
                {"error": "All fields are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    username = validated_data.get('username')
    password = validated_data.get('password')
    
    # Use the service layer for business logic
    success, response_data = AuthService.register_user(
        username=username,
        password=password
    )
    
    if success:
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    else:
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login_user(request):
    """
    Authenticate and login a user.
    
    Args:
        request: HTTP request containing username and password in data.
    
    Returns:
        JsonResponse with authentication token and username or error.
    """
    # Use serializer for validation
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        # For invalid login data, return generic invalid credentials error
        return JsonResponse(
            {"error": "Invalid credentials"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    username = validated_data.get('username')
    password = validated_data.get('password')
    
    # Use the service layer for business logic
    success, response_data = AuthService.login_user(
        username=username,
        password=password
    )
    
    if success:
        return JsonResponse(response_data, status=status.HTTP_200_OK)
    else:
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def logout_user(request):
    """
    Logout a user by deleting their authentication token.
    
    Args:
        request: HTTP request with authentication token.
    
    Returns:
        JsonResponse with success message or error.
    """
    # Use the service layer for business logic
    success, response_data = AuthService.logout_user(request.auth)
    
    if success:
        return JsonResponse(response_data, status=status.HTTP_200_OK)
    else:
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
