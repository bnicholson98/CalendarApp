"""
Tests for concurrency and transaction handling.
"""
import threading
from datetime import datetime, timedelta
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from core.models import Event


class ConcurrencyAndTransactionTests(TransactionTestCase):
    """Test concurrent operations and transaction handling."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')
        self.token1, _ = Token.objects.get_or_create(user=self.user1)
        self.token2, _ = Token.objects.get_or_create(user=self.user2)
        self.create_event_url = reverse('events:create')
    
    def test_concurrent_event_creation(self):
        """Test creating events from multiple users concurrently."""
        # Simulate creating events from two users concurrently
        client1 = APIClient()
        client2 = APIClient()
        client1.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        client2.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        date1 = datetime.now().date().strftime('%Y-%m-%d')
        date2 = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        payload1 = {
            'event_name': 'User1 Event',
            'dates': [date1, date2]
        }
        payload2 = {
            'event_name': 'User2 Event',
            'dates': [date1, date2]
        }
        
        # Create events concurrently
        def create_event(client, payload):
            client.post(self.create_event_url, payload, format='json')
        
        t1 = threading.Thread(target=create_event, args=(client1, payload1))
        t2 = threading.Thread(target=create_event, args=(client2, payload2))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        # Verify both events were created correctly
        self.assertEqual(Event.objects.count(), 4)
        self.assertEqual(Event.objects.filter(user=self.user1, event_name='User1 Event').count(), 2)
        self.assertEqual(Event.objects.filter(user=self.user2, event_name='User2 Event').count(), 2)
