"""
Authentication-related views for user registration, login, and logout.
"""
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication

from core.serializers import UserRegistrationSerializer, LoginSerializer
from core.services.auth_service import AuthService
from core.exceptions import ValidationError, ExistingUserError


@api_view(["POST"])
def register_user(request):
    """
    Register a new user.
    
    Args:
        request: HTTP request containing username and password in data.
    
    Returns:
        Response with success message or error.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:
        response_data = AuthService.register_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return Response(response_data, status=status.HTTP_201_CREATED)
    except (ValidationError, ExistingUserError) as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login_user(request):
    """
    Authenticate and login a user.
    
    Args:
        request: HTTP request containing username and password in data.
    
    Returns:
        Response with authentication token and username or error.
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    
    try:
        response_data = AuthService.login_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return Response(response_data, status=status.HTTP_200_OK)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
def logout_user(request):
    """
    Logout a user by deleting their authentication token.
    
    Args:
        request: HTTP request with authentication token.
    
    Returns:
        Response with success message or error.
    """
    try:
        AuthService.logout_user(request.auth)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ValidationError as e:
        return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
