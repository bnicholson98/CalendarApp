"""
Tests for concurrency and transaction handling.
"""
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from core.models import Event, ProposedDate


class ConcurrencyAndTransactionTests(APITestCase):
    """Test concurrent operations and transaction handling."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')
        self.token1, _ = Token.objects.get_or_create(user=self.user1)
        self.token2, _ = Token.objects.get_or_create(user=self.user2)
        self.create_event_url = reverse('events:create')
    
    def test_multiple_user_event_creation(self):
        """Test creating events from multiple users."""
        # Create events from two different users
        client1 = APIClient()
        client2 = APIClient()
        client1.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        client2.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        date1 = datetime.now().date().strftime('%Y-%m-%d')
        date2 = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        payload1 = {
            'event_name': 'User1 Event',
            'proposed_dates': [date1, date2]
        }
        payload2 = {
            'event_name': 'User2 Event',
            'proposed_dates': [date1, date2]
        }
        
        # Create events for user1
        response1 = client1.post(self.create_event_url, payload1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Create events for user2
        response2 = client2.post(self.create_event_url, payload2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both events were created correctly
        # Now we have 2 events (one per user), each with 2 proposed dates
        self.assertEqual(Event.objects.count(), 2)
        self.assertEqual(Event.objects.filter(user=self.user1, event_name='User1 Event').count(), 1)
        self.assertEqual(Event.objects.filter(user=self.user2, event_name='User2 Event').count(), 1)
        
        # Each event should have 2 proposed dates
        user1_event = Event.objects.get(user=self.user1)
        user2_event = Event.objects.get(user=self.user2)
        self.assertEqual(user1_event.proposed_dates.count(), 2)
        self.assertEqual(user2_event.proposed_dates.count(), 2)
