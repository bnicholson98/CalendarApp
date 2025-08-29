"""
Tests for model functionality.
"""
from datetime import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Event
from core.serializers import EventSerializer


class EventModelTests(TestCase):
    """Test Event model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = datetime.now().date()
        
    def test_event_creation(self):
        """Test creating an Event instance."""
        event = Event.objects.create(
            event_name='Test Event',
            user=self.user,
            date=self.today
        )
        self.assertEqual(event.event_name, 'Test Event')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.date, self.today)


class EventSerializerTests(TestCase):
    """Test Event serializer functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = datetime.now().date()
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.user,
            date=self.today
        )
        self.serializer = EventSerializer(instance=self.event)
        
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields."""
        data = self.serializer.data
        self.assertIn('id', data)
        self.assertIn('event_name', data)
        self.assertIn('user', data)
        self.assertIn('date', data)