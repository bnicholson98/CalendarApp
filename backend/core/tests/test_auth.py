"""
Tests for authentication-related functionality.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status

from core.throttles import LoginRateThrottle, RegisterRateThrottle


class UserRegistrationTests(TestCase):
    """Test user registration functionality."""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('auth:register')
        self.valid_payload = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        self.invalid_payload_no_username = {
            'password': 'testpass123'
        }
        self.invalid_payload_no_password = {
            'username': 'testuser'
        }

    def test_valid_registration(self):
        """Test successful user registration."""
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_invalid_registration_no_username(self):
        """Test registration without username fails."""
        response = self.client.post(
            self.register_url,
            self.invalid_payload_no_username,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_invalid_registration_no_password(self):
        """Test registration without password fails."""
        response = self.client.post(
            self.register_url,
            self.invalid_payload_no_password,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_duplicate_user_registration(self):
        """Test duplicate username registration fails."""
        # Create user first
        User.objects.create_user(username='testuser', password='testpass123')
        
        # Try to create same user again
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)


class UserLoginTests(TestCase):
    """Test user login functionality."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('auth:login')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.valid_payload = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        self.invalid_payload_wrong_password = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        self.invalid_payload_wrong_username = {
            'username': 'wronguser',
            'password': 'testpass123'
        }

    def test_valid_login(self):
        """Test successful user login returns token."""
        response = self.client.post(
            self.login_url,
            self.valid_payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())
        self.assertIn('userName', response.json())
        self.assertEqual(response.json()['userName'], 'testuser')

    def test_invalid_login_wrong_password(self):
        """Test login with wrong password fails."""
        response = self.client.post(
            self.login_url,
            self.invalid_payload_wrong_password,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())

    def test_invalid_login_wrong_username(self):
        """Test login with wrong username fails."""
        response = self.client.post(
            self.login_url,
            self.invalid_payload_wrong_username,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())


class UserLogoutTests(APITestCase):
    """Test user logout functionality."""
    
    def setUp(self):
        self.logout_url = reverse('auth:logout')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.api_client = APIClient()

    def test_valid_logout(self):
        """Test successful logout deletes token."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.api_client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_invalid_logout_no_token(self):
        """Test logout without token fails."""
        response = self.api_client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_logout_bad_token(self):
        """Test logout with invalid token fails."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token badtoken123')
        response = self.api_client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthRateLimitTests(TestCase):
    """Test rate limiting on the unauthenticated auth endpoints."""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('auth:login')
        self.register_url = reverse('auth:register')
        User.objects.create_user(username='testuser', password='testpass123')

    def test_login_throttled_after_limit(self):
        """Test login returns 429 once the per-IP limit is used up."""
        limit = LoginRateThrottle().num_requests
        payload = {'username': 'testuser', 'password': 'wrongpass'}

        for _ in range(limit):
            response = self.client.post(self.login_url, payload, content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.login_url, payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', response)

    def test_throttled_login_rejects_valid_credentials(self):
        """Test a throttled client cannot log in even with the right password."""
        limit = LoginRateThrottle().num_requests

        for _ in range(limit):
            self.client.post(
                self.login_url,
                {'username': 'testuser', 'password': 'wrongpass'},
                content_type='application/json'
            )

        response = self.client.post(
            self.login_url,
            {'username': 'testuser', 'password': 'testpass123'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertNotIn('token', response.json())

    def test_register_throttled_after_limit(self):
        """Test registration returns 429 once the per-IP limit is used up."""
        limit = RegisterRateThrottle().num_requests

        for i in range(limit):
            response = self.client.post(
                self.register_url,
                {'username': f'newuser{i}', 'password': 'testpass123'},
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.register_url,
            {'username': 'onetoomany', 'password': 'testpass123'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(User.objects.filter(username='onetoomany').exists())

    def test_login_and_register_limits_are_separate(self):
        """Test using up the login limit does not block registration."""
        limit = LoginRateThrottle().num_requests

        for _ in range(limit + 1):
            self.client.post(
                self.login_url,
                {'username': 'testuser', 'password': 'wrongpass'},
                content_type='application/json'
            )

        response = self.client.post(
            self.register_url,
            {'username': 'newuser', 'password': 'testpass123'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
