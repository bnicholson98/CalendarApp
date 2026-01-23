"""
Service layer for authentication-related business logic.
"""
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from typing import Optional, Dict

from core.exceptions import ValidationError, ExistingUserError


class AuthService:
    """Service class for handling authentication business logic."""
    
    @staticmethod
    def register_user(username: str, password: str) -> Dict[str, str]:
        """
        Register a new user.
        
        Args:
            username: The username for the new user.
            password: The password for the new user.
        
        Returns:
            Dict with success message.
            
        Raises:
            ExistingUserError: If user already exists.
            ValidationError: If creation fails.
        """
        if User.objects.filter(username=username).exists():
            raise ExistingUserError("User already exists")
        
        try:
            User.objects.create_user(username=username, password=password)
            return {"message": "User created successfully"}
        except Exception as e:
            raise ValidationError(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def login_user(username: str, password: str) -> Dict[str, str]:
        """
        Authenticate and login a user.
        
        Args:
            username: The username to authenticate.
            password: The password to authenticate.
        
        Returns:
            Dict with token and username.
            
        Raises:
            ValidationError: If credentials are invalid.
        """
        user = authenticate(username=username, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return {
                "token": token.key,
                "userId": user.id,
                "userName": username
            }
        
        raise ValidationError("Invalid credentials")
    
    @staticmethod
    def logout_user(token: Optional[Token]) -> Dict[str, str]:
        """
        Logout a user by deleting their authentication token.
        
        Args:
            token: The authentication token to delete.
        
        Returns:
            Dict with success message.
            
        Raises:
            ValidationError: If token is invalid.
        """
        if token:
            token.delete()
            return {"message": "Logged out successfully"}
        
        raise ValidationError("Invalid token")
