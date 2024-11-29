from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated


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
        return JsonResponse({"token": token.key}, status=status.HTTP_200_OK)
    
    return JsonResponse({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def logout_user(request):
    token = request.auth

    if token:
        token.delete()
        return JsonResponse({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    
    return JsonResponse({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)