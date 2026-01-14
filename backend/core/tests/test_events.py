"""
Tests for event-related functionality.
"""
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from core.models import Event, ProposedDate


class EventCreationTests(APITestCase):
    """Test event creation functionality."""
    
    def setUp(self):
        self.create_event_url = reverse('events:create')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        
        self.valid_payload = {
            'event_name': 'Test Event',
            'proposed_dates': [
                self.today.strftime('%Y-%m-%d'),
                self.tomorrow.strftime('%Y-%m-%d')
            ]
        }
        self.invalid_payload_no_name = {
            'proposed_dates': [self.today.strftime('%Y-%m-%d')]
        }
        self.invalid_payload_no_dates = {
            'event_name': 'Test Event'
        }
        self.invalid_payload_bad_date_format = {
            'event_name': 'Test Event',
            'proposed_dates': ['01-01-2023']  # Wrong format
        }

    def test_valid_event_creation(self):
        """Test successful event creation with multiple proposed dates."""
        response = self.api_client.post(
            self.create_event_url,
            self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()
        self.assertEqual(event.event_name, 'Test Event')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.status, Event.Status.PROPOSED)
        self.assertEqual(event.proposed_dates.count(), 2)

    def test_unauthorized_event_creation(self):
        """Test event creation without authentication fails."""
        client = APIClient()  # Client without token
        response = client.post(
            self.create_event_url,
            self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Event.objects.count(), 0)

    def test_invalid_event_creation_no_name(self):
        """Test event creation without name fails."""
        response = self.api_client.post(
            self.create_event_url,
            self.invalid_payload_no_name,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Event.objects.count(), 0)

    def test_invalid_event_creation_no_dates(self):
        """Test event creation without dates fails."""
        response = self.api_client.post(
            self.create_event_url,
            self.invalid_payload_no_dates,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Event.objects.count(), 0)

    def test_invalid_event_creation_bad_date_format(self):
        """Test event creation with invalid date format fails."""
        response = self.api_client.post(
            self.create_event_url,
            self.invalid_payload_bad_date_format,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Event.objects.count(), 0)


class EventListEndpointTests(APITestCase):
    """Test the list events endpoint comprehensively."""
    
    def setUp(self):
        self.list_url = reverse('events:list')
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.token1, _ = Token.objects.get_or_create(user=self.user1)
        self.token2, _ = Token.objects.get_or_create(user=self.user2)
        
        self.api_client = APIClient()
    
    def test_list_events_authenticated(self):
        """Test listing events for authenticated user."""
        # Create events for user1
        for i in range(5):
            event = Event.objects.create(
                event_name=f'Event {i}',
                user=self.user1
            )
            ProposedDate.objects.create(
                event=event,
                date=datetime.now().date() + timedelta(days=i)
            )
        
        # Create events for user2 (should not be returned)
        other_event = Event.objects.create(
            event_name='Other User Event',
            user=self.user2
        )
        ProposedDate.objects.create(
            event=other_event,
            date=datetime.now().date()
        )
        
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.api_client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
        # Verify all events belong to user1
        for event in response.data:
            self.assertIn('Event', event['event_name'])
            self.assertEqual(event['user'], self.user1.id)
    
    def test_list_events_unauthenticated(self):
        """Test listing events without authentication."""
        response = self.api_client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_events_empty(self):
        """Test listing events when user has no events."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.api_client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class EventDetailEndpointTests(APITestCase):
    """Test the get event detail endpoint."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.other_token, _ = Token.objects.get_or_create(user=self.other_user)
        
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.user
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
        
        self.other_event = Event.objects.create(
            event_name='Other User Event',
            user=self.other_user
        )
        ProposedDate.objects.create(
            event=self.other_event,
            date=datetime.now().date()
        )
        
        self.api_client = APIClient()
    
    def test_get_event_success(self):
        """Test retrieving a specific event successfully."""
        url = reverse('events:detail', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.event.id)
        self.assertEqual(response.data['event_name'], 'Test Event')
        self.assertEqual(response.data['status'], 'PROPOSED')
    
    def test_get_event_not_found(self):
        """Test retrieving non-existent event."""
        url = reverse('events:detail', args=[99999])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Event not found"})
    
    def test_get_event_unauthorized(self):
        """Test retrieving event without authentication."""
        url = reverse('events:detail', args=[self.event.id])
        
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EventUpdateEndpointTests(APITestCase):
    """Test the update event endpoint comprehensively."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.other_token, _ = Token.objects.get_or_create(user=self.other_user)
        
        self.event = Event.objects.create(
            event_name='Original Event',
            user=self.user
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
        
        self.api_client = APIClient()
    
    def test_update_event_success(self):
        """Test successful event update."""
        url = reverse('events:update', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        update_data = {
            'event_name': 'Updated Event'
        }
        
        response = self.api_client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_name'], 'Updated Event')
        
        # Verify database update
        self.event.refresh_from_db()
        self.assertEqual(self.event.event_name, 'Updated Event')
    
    def test_update_event_not_found(self):
        """Test updating non-existent event."""
        url = reverse('events:update', args=[99999])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        update_data = {'event_name': 'Updated Event'}
        response = self.api_client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Event not found"})
    
    def test_update_event_unauthorized(self):
        """Test updating event without authentication."""
        url = reverse('events:update', args=[self.event.id])
        
        update_data = {'event_name': 'Updated Event'}
        response = self.api_client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_event_empty_name(self):
        """Test updating event with empty name."""
        url = reverse('events:update', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        update_data = {'event_name': ''}
        response = self.api_client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventDeleteEndpointTests(APITestCase):
    """Test the delete event endpoint comprehensively."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.other_token, _ = Token.objects.get_or_create(user=self.other_user)
        
        self.api_client = APIClient()
    
    def test_delete_event_success(self):
        """Test successful event deletion."""
        event = Event.objects.create(
            event_name='Event to Delete',
            user=self.user
        )
        ProposedDate.objects.create(
            event=event,
            date=datetime.now().date()
        )
        event_id = event.id
        
        url = reverse('events:delete', args=[event_id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=event_id).exists())
    
    def test_delete_event_not_found(self):
        """Test deleting non-existent event."""
        url = reverse('events:delete', args=[99999])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Event not found"})
    
    def test_delete_event_unauthorized(self):
        """Test deleting event without authentication."""
        event = Event.objects.create(
            event_name='Event',
            user=self.user
        )
        
        url = reverse('events:delete', args=[event.id])
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Event.objects.filter(id=event.id).exists())


class EventEdgeCaseTests(APITestCase):
    """Test edge cases for event management."""
    
    def setUp(self):
        self.create_event_url = reverse('events:create')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_very_long_event_name(self):
        """Test event creation with maximum length name."""
        long_name = 'A' * 255  # Max length per model definition
        date = datetime.now().date().strftime('%Y-%m-%d')
        payload = {
            'event_name': long_name,
            'proposed_dates': [date]
        }
        response = self.api_client.post(
            self.create_event_url,
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.first().event_name, long_name)

    def test_many_proposed_dates(self):
        """Test event creation with multiple proposed dates."""
        dates = [(datetime.now().date() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(50)]
        payload = {
            'event_name': 'Multi-Date Event',
            'proposed_dates': dates
        }
        response = self.api_client.post(
            self.create_event_url,
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.first()
        self.assertEqual(event.proposed_dates.count(), 50)

    def test_empty_dates_list(self):
        """Test event creation with empty dates list fails."""
        payload = {
            'event_name': 'No Dates Event',
            'proposed_dates': []
        }
        response = self.api_client.post(
            self.create_event_url,
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_past_date(self):
        """Test event creation with past date."""
        past_date = (datetime.now().date() - timedelta(days=365)).strftime('%Y-%m-%d')
        payload = {
            'event_name': 'Past Event',
            'proposed_dates': [past_date]
        }
        response = self.api_client.post(
            self.create_event_url,
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # Application allows past dates

    def test_special_characters_in_event_name(self):
        """Test event creation with special characters in name."""
        special_name = "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/"
        date = datetime.now().date().strftime('%Y-%m-%d')
        payload = {
            'event_name': special_name,
            'proposed_dates': [date]
        }
        response = self.api_client.post(
            self.create_event_url,
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.first().event_name, special_name)


class EventStatusAndDatesTests(APITestCase):
    """Tests for confirm/cancel and proposed-date endpoints."""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.invitee = User.objects.create_user(username='invitee', password='pass')
        self.owner_token, _ = Token.objects.get_or_create(user=self.owner)
        self.invitee_token, _ = Token.objects.get_or_create(user=self.invitee)
        self.api_client = APIClient()

        # Create event with two proposed dates and an invite
        self.event = Event.objects.create(event_name='Status Event', user=self.owner)
        self.date1 = ProposedDate.objects.create(event=self.event, date=datetime.now().date())
        self.date2 = ProposedDate.objects.create(event=self.event, date=(datetime.now().date() + timedelta(days=1)))
        from core.models import EventInvite
        EventInvite.objects.create(event=self.event, owner=self.owner, invitee=self.invitee)

    def test_confirm_event_success(self):
        url = reverse('events:confirm', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        resp = self.api_client.post(url, {'proposed_date_id': self.date1.id}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.Status.CONFIRMED)
        self.assertEqual(self.event.confirmed_date.id, self.date1.id)

    def test_confirm_event_not_owner(self):
        url = reverse('events:confirm', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        resp = self.api_client.post(url, {'proposed_date_id': self.date1.id}, format='json')

        # Only owner may confirm; view returns 404 when not owner
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_confirm_event_invalid_date(self):
        url = reverse('events:confirm', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        resp = self.api_client.post(url, {'proposed_date_id': 99999}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_event_success(self):
        url = reverse('events:cancel', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        resp = self.api_client.post(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.Status.CANCELLED)

    def test_cancel_event_not_owner(self):
        url = reverse('events:cancel', args=[self.event.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        resp = self.api_client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_proposed_dates_owner_and_invitee(self):
        url = reverse('events:list_dates', args=[self.event.id])

        # Owner
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        resp_owner = self.api_client.get(url)
        self.assertEqual(resp_owner.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp_owner.data, list)
        self.assertEqual(len(resp_owner.data), 2)

        # Invitee
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        resp_inv = self.api_client.get(url)
        self.assertEqual(resp_inv.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_inv.data), 2)

    def test_add_proposed_date_success_and_not_owner(self):
        url = reverse('events:add_date', args=[self.event.id])
        new_date = (datetime.now().date() + timedelta(days=5)).strftime('%Y-%m-%d')

        # Owner can add
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        resp = self.api_client.post(url, {'date': new_date}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.event.proposed_dates.count(), 3)

        # Invitee cannot add
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        resp2 = self.api_client.post(url, {'date': (datetime.now().date() + timedelta(days=6)).strftime('%Y-%m-%d')}, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_proposed_date_success_and_edge_cases(self):
        # Remove one of two dates (owner)
        url = reverse('events:remove_date', args=[self.event.id, self.date1.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        resp = self.api_client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.event.proposed_dates.count(), 1)

        # Cannot remove last proposed date
        last_date = self.event.proposed_dates.first()
        url2 = reverse('events:remove_date', args=[self.event.id, last_date.id])
        resp2 = self.api_client.delete(url2)
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
