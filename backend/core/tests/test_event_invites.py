"""
Tests for event invite-related functionality.
"""
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from core.models import Event, EventInvite, ProposedDate


class EventInviteModelTests(TestCase):
    """Test EventInvite model functionality."""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        )
        self.invitee = User.objects.create_user(
            username='invitee',
            password='testpass123'
        )
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.owner
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
    
    def test_invite_creation(self):
        """Test creating an EventInvite instance."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee,
            status=EventInvite.Status.PENDING
        )
        self.assertEqual(invite.event, self.event)
        self.assertEqual(invite.owner, self.owner)
        self.assertEqual(invite.invitee, self.invitee)
        self.assertEqual(invite.status, EventInvite.Status.PENDING)
        self.assertIsNotNone(invite.created_at)
        self.assertIsNotNone(invite.updated_at)
    
    def test_invite_cascade_delete_on_event_delete(self):
        """Test that invites are deleted when the event is deleted."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        invite_id = invite.id
        
        # Delete the event
        self.event.delete()
        
        # Verify invite is also deleted
        self.assertFalse(EventInvite.objects.filter(id=invite_id).exists())
    
    def test_invite_unique_together_constraint(self):
        """Test that duplicate invites are not allowed."""
        EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        # Try to create duplicate invite
        with self.assertRaises(Exception):
            EventInvite.objects.create(
                event=self.event,
                owner=self.owner,
                invitee=self.invitee
            )
    
    def test_invite_status_choices(self):
        """Test all status choices are valid."""
        for status_choice in EventInvite.Status.choices:
            invite = EventInvite.objects.create(
                event=self.event,
                owner=self.owner,
                invitee=User.objects.create_user(
                    username=f'user_{status_choice[0]}',
                    password='testpass123'
                ),
                status=status_choice[0]
            )
            self.assertEqual(invite.status, status_choice[0])


class EventInviteCreationTests(APITestCase):
    """Test event invite creation functionality."""
    
    def setUp(self):
        self.create_invite_url = reverse('event_invites:create')
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        )
        self.invitee = User.objects.create_user(
            username='invitee',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        self.owner_token, _ = Token.objects.get_or_create(user=self.owner)
        self.invitee_token, _ = Token.objects.get_or_create(user=self.invitee)
        self.other_token, _ = Token.objects.get_or_create(user=self.other_user)
        
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.owner
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
        
        self.api_client = APIClient()
    
    def test_valid_invite_creation(self):
        """Test successful invite creation by event owner."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.post(
            self.create_invite_url,
            {'event': self.event.id, 'invitee': self.invitee.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EventInvite.objects.count(), 1)
        invite = EventInvite.objects.first()
        self.assertEqual(invite.event, self.event)
        self.assertEqual(invite.owner, self.owner)
        self.assertEqual(invite.invitee, self.invitee)
        self.assertEqual(invite.status, EventInvite.Status.PENDING)
    
    def test_invite_creation_by_non_owner_fails(self):
        """Test that non-owner cannot create invites."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        
        response = self.api_client.post(
            self.create_invite_url,
            {'event': self.event.id, 'invitee': self.invitee.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EventInvite.objects.count(), 0)
    
    def test_owner_cannot_invite_themselves(self):
        """Test that owner cannot invite themselves."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.post(
            self.create_invite_url,
            {'event': self.event.id, 'invitee': self.owner.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EventInvite.objects.count(), 0)
    
    def test_duplicate_invite_fails(self):
        """Test that duplicate invites are rejected."""
        # Create first invite
        EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.post(
            self.create_invite_url,
            {'event': self.event.id, 'invitee': self.invitee.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(EventInvite.objects.count(), 1)
    
    def test_unauthorized_invite_creation(self):
        """Test invite creation without authentication fails."""
        response = self.api_client.post(
            self.create_invite_url,
            {'event': self.event.id, 'invitee': self.invitee.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(EventInvite.objects.count(), 0)
    
    def test_invite_creation_missing_fields(self):
        """Test invite creation with missing fields fails."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        # Missing invitee
        response = self.api_client.post(
            self.create_invite_url,
            {'event': self.event.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing event
        response = self.api_client.post(
            self.create_invite_url,
            {'invitee': self.invitee.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventInviteListTests(APITestCase):
    """Test event invite list endpoints."""
    
    def setUp(self):
        self.list_received_url = reverse('event_invites:list_received')
        self.list_sent_url = reverse('event_invites:list_sent')
        
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        )
        self.invitee = User.objects.create_user(
            username='invitee',
            password='testpass123'
        )
        self.owner_token, _ = Token.objects.get_or_create(user=self.owner)
        self.invitee_token, _ = Token.objects.get_or_create(user=self.invitee)
        
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.owner
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
        
        self.invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        self.api_client = APIClient()
    
    def test_list_received_invites(self):
        """Test listing received invites."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.get(self.list_received_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.invite.id)
    
    def test_list_sent_invites(self):
        """Test listing sent invites."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.get(self.list_sent_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.invite.id)
    
    def test_list_invites_empty(self):
        """Test listing invites when none exist."""
        # Delete existing invite
        self.invite.delete()
        
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.get(self.list_received_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    def test_list_invites_unauthenticated(self):
        """Test listing invites without authentication."""
        response = self.api_client.get(self.list_received_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.api_client.get(self.list_sent_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EventInviteDetailTests(APITestCase):
    """Test event invite detail endpoint."""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        )
        self.invitee = User.objects.create_user(
            username='invitee',
            password='testpass123'
        )
        self.owner_token, _ = Token.objects.get_or_create(user=self.owner)
        self.invitee_token, _ = Token.objects.get_or_create(user=self.invitee)
        
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.owner
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
        
        self.invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        self.api_client = APIClient()
    
    def test_get_invite_success(self):
        """Test retrieving a specific invite."""
        url = reverse('event_invites:detail', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.invite.id)
    
    def test_get_invite_not_found(self):
        """Test retrieving non-existent invite."""
        url = reverse('event_invites:detail', args=[99999])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_invite_unauthenticated(self):
        """Test retrieving invite without authentication."""
        url = reverse('event_invites:detail', args=[self.invite.id])
        
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EventInviteUpdateTests(APITestCase):
    """Test event invite update endpoint."""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        )
        self.invitee = User.objects.create_user(
            username='invitee',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        self.owner_token, _ = Token.objects.get_or_create(user=self.owner)
        self.invitee_token, _ = Token.objects.get_or_create(user=self.invitee)
        self.other_token, _ = Token.objects.get_or_create(user=self.other_user)
        
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.owner
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
        
        self.invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        self.api_client = APIClient()
    
    def test_update_invite_status_accepted(self):
        """Test invitee can accept invite."""
        url = reverse('event_invites:update', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.put(
            url,
            {'status': 'ACCEPTED'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, EventInvite.Status.ACCEPTED)
    
    def test_update_invite_status_declined(self):
        """Test invitee can decline invite."""
        url = reverse('event_invites:update', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.put(
            url,
            {'status': 'DECLINED'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, EventInvite.Status.DECLINED)
    
    def test_update_invite_status_maybe(self):
        """Test invitee can set status to maybe."""
        url = reverse('event_invites:update', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.put(
            url,
            {'status': 'MAYBE'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, EventInvite.Status.MAYBE)
    
    def test_update_invite_by_owner_fails(self):
        """Test that owner cannot update invite status."""
        url = reverse('event_invites:update', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.put(
            url,
            {'status': 'ACCEPTED'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, EventInvite.Status.PENDING)
    
    def test_update_invite_by_other_user_fails(self):
        """Test that other users cannot update invite status."""
        url = reverse('event_invites:update', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        
        response = self.api_client.put(
            url,
            {'status': 'ACCEPTED'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_invite_invalid_status(self):
        """Test updating with invalid status fails."""
        url = reverse('event_invites:update', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.put(
            url,
            {'status': 'INVALID'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_invite_not_found(self):
        """Test updating non-existent invite."""
        url = reverse('event_invites:update', args=[99999])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.put(
            url,
            {'status': 'ACCEPTED'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_invite_missing_status(self):
        """Test updating without status fails."""
        url = reverse('event_invites:update', args=[self.invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.put(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventInviteDeleteTests(APITestCase):
    """Test event invite delete endpoint."""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        )
        self.invitee = User.objects.create_user(
            username='invitee',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        self.owner_token, _ = Token.objects.get_or_create(user=self.owner)
        self.invitee_token, _ = Token.objects.get_or_create(user=self.invitee)
        self.other_token, _ = Token.objects.get_or_create(user=self.other_user)
        
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.owner
        )
        ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
        
        self.api_client = APIClient()
    
    def test_delete_invite_by_owner(self):
        """Test owner can delete invite."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        invite_id = invite.id
        
        url = reverse('event_invites:delete', args=[invite_id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EventInvite.objects.filter(id=invite_id).exists())
    
    def test_delete_invite_by_invitee_fails(self):
        """Test invitee cannot delete invite."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        url = reverse('event_invites:delete', args=[invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(EventInvite.objects.filter(id=invite.id).exists())
    
    def test_delete_invite_by_other_user_fails(self):
        """Test other users cannot delete invite."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        url = reverse('event_invites:delete', args=[invite.id])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_invite_not_found(self):
        """Test deleting non-existent invite."""
        url = reverse('event_invites:delete', args=[99999])
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_invite_unauthenticated(self):
        """Test deleting invite without authentication."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        url = reverse('event_invites:delete', args=[invite.id])
        
        response = self.api_client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
