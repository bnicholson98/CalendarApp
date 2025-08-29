"""
Integration tests for complete user workflows.
"""
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from core.models import Event


class UserJourneyIntegrationTests(APITestCase):
    """Test complete user journey from registration to event creation."""
    
    def setUp(self):
        self.register_url = reverse('auth:register')
        self.login_url = reverse('auth:login')
        self.logout_url = reverse('auth:logout')
        self.create_event_url = reverse('events:create')
        self.api_client = APIClient()
        
        self.user_data = {
            'username': 'integrationuser',
            'password': 'integration123'
        }
        
        self.today = datetime.now().date()
        self.event_data = {
            'event_name': 'Integration Event',
            'dates': [self.today.strftime('%Y-%m-%d')]
        }
        
    def test_full_user_journey(self):
        """Test complete workflow: register -> login -> create event -> logout."""
        # 1. Register user
        register_response = self.api_client.post(
            self.register_url,
            self.user_data,
            format='json'
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        # 2. Login user
        login_response = self.api_client.post(
            self.login_url,
            self.user_data,
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('token', login_response.json())
        token = login_response.json()['token']
        
        # 3. Logout user
        logout_response = self.api_client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # 4. Verify can't create event after logout
        event_after_logout_response = self.api_client.post(
            self.create_event_url,
            self.event_data,
            format='json'
        )
        self.assertEqual(event_after_logout_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Event.objects.count(), 1)  # No new event created
