"""
Service layer for authentication-related business logic.
"""
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from typing import Optional, Dict, Tuple


class AuthService:
    """Service class for handling authentication business logic."""
    
    @staticmethod
    def register_user(username: str, password: str) -> Tuple[bool, Dict[str, str]]:
        """
        Register a new user.
        
        Args:
            username: The username for the new user.
            password: The password for the new user.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        if not username or not password:
            return False, {"error": "All fields are required"}
        
        if User.objects.filter(username=username).exists():
            return False, {"error": "User already exists"}
        
        try:
            user = User.objects.create_user(username=username, password=password)
            return True, {"message": "User created successfully"}
        except Exception as e:
            return False, {"error": f"Failed to create user: {str(e)}"}
    
    @staticmethod
    def login_user(username: str, password: str) -> Tuple[bool, Dict[str, str]]:
        """
        Authenticate and login a user.
        
        Args:
            username: The username to authenticate.
            password: The password to authenticate.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        user = authenticate(username=username, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return True, {
                "token": token.key,
                "userName": username
            }
        
        return False, {"error": "Invalid credentials"}
    
    @staticmethod
    def logout_user(token: Optional[Token]) -> Tuple[bool, Dict[str, str]]:
        """
        Logout a user by deleting their authentication token.
        
        Args:
            token: The authentication token to delete.
        
        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        if token:
            token.delete()
            return True, {"message": "Logged out successfully"}
        
        return False, {"error": "Invalid token"}
