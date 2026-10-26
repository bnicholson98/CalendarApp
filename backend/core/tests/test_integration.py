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
            'proposed_dates': [self.today.strftime('%Y-%m-%d')]
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
        
        # Set credentials for subsequent requests
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # 3. Logout user
        logout_response = self.api_client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 4. Verify can't create event after logout
        event_after_logout_response = self.api_client.post(
            self.create_event_url,
            self.event_data,
            format='json'
        )
        self.assertEqual(event_after_logout_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Event.objects.count(), 0)  # No new event created


class EventProposalIntegrationTests(APITestCase):
    """Integration tests for the event proposal workflow."""
    
    def setUp(self):
        self.register_url = reverse('auth:register')
        self.login_url = reverse('auth:login')
        self.create_event_url = reverse('events:create')
        self.api_client = APIClient()
        
        # Create owner and invitees
        self.owner = User.objects.create_user(username='owner', password='ownerpass')
        self.invitee1 = User.objects.create_user(username='invitee1', password='inviteepass')
        self.invitee2 = User.objects.create_user(username='invitee2', password='inviteepass')
        
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.day_after = self.today + timedelta(days=2)
    
    def test_full_event_proposal_workflow(self):
        """Test complete event proposal workflow."""
        # 1. Owner logs in
        owner_login = self.api_client.post(
            self.login_url,
            {'username': 'owner', 'password': 'ownerpass'},
            format='json'
        )
        owner_token = owner_login.json()['token']
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {owner_token}')
        
        # 2. Owner creates event proposal with invitees
        event_data = {
            'event_name': 'Team Planning',
            'proposed_dates': [
                self.today.strftime('%Y-%m-%d'),
                self.tomorrow.strftime('%Y-%m-%d'),
                self.day_after.strftime('%Y-%m-%d')
            ],
            'invitees': [self.invitee1.username, self.invitee2.username]
        }
        
        create_response = self.api_client.post(
            self.create_event_url,
            event_data,
            format='json'
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        event_id = create_response.data['event_id']
        
        # 3. Verify event was created with correct data
        event = Event.objects.get(id=event_id)
        self.assertEqual(event.status, Event.Status.PROPOSED)
        self.assertEqual(event.proposed_dates.count(), 3)
        self.assertEqual(event.invites.count(), 2)
        
        # 4. Invitee1 logs in and votes
        invitee1_login = self.api_client.post(
            self.login_url,
            {'username': 'invitee1', 'password': 'inviteepass'},
            format='json'
        )
        invitee1_token = invitee1_login.json()['token']
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {invitee1_token}')
        
        # Invitee1 votes on dates
        proposed_dates = list(event.proposed_dates.all())
        for i, pd in enumerate(proposed_dates):
            vote_url = reverse('votes:vote', args=[event_id, pd.id])
            availability = 'AVAILABLE' if i < 2 else 'NOT_AVAILABLE'
            self.api_client.post(vote_url, {'availability': availability}, format='json')
        
        # 5. Invitee2 logs in and votes
        invitee2_login = self.api_client.post(
            self.login_url,
            {'username': 'invitee2', 'password': 'inviteepass'},
            format='json'
        )
        invitee2_token = invitee2_login.json()['token']
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {invitee2_token}')
        
        for i, pd in enumerate(proposed_dates):
            vote_url = reverse('votes:vote', args=[event_id, pd.id])
            availability = 'AVAILABLE' if i == 1 else 'MAYBE'
            self.api_client.post(vote_url, {'availability': availability}, format='json')
        
        # 6. Owner checks votes and confirms event
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {owner_token}')
        
        votes_url = reverse('votes:list', args=[event_id])
        votes_response = self.api_client.get(votes_url)
        self.assertEqual(votes_response.status_code, status.HTTP_200_OK)
        
        # 7. Owner confirms the event with the most popular date (tomorrow)
        confirm_url = reverse('events:confirm', args=[event_id])
        confirm_response = self.api_client.post(
            confirm_url,
            {'proposed_date_id': proposed_dates[1].id},
            format='json'
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        
        # 8. Verify event is confirmed
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CONFIRMED)
        self.assertEqual(event.confirmed_date.id, proposed_dates[1].id)

    def test_create_event_self_invite_warning(self):
        """Owner's own username in invitees is silently dropped; event still created with remaining invitees."""
        owner_login = self.api_client.post(
            self.login_url,
            {'username': 'owner', 'password': 'ownerpass'},
            format='json'
        )
        owner_token = owner_login.json()['token']
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {owner_token}')

        event_data = {
            'event_name': 'Self Invite Test',
            'proposed_dates': [self.today.strftime('%Y-%m-%d')],
            'invitees': ['owner', 'invitee1'],  # owner included deliberately
        }

        resp = self.api_client.post(self.create_event_url, event_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        event = Event.objects.get(id=resp.data['event_id'])
        # Only invitee1 should have received an invite; owner was dropped
        self.assertEqual(event.invites.count(), 1)
        self.assertEqual(event.invites.first().invitee.username, 'invitee1')

        # Response must contain a self_invited warning
        warnings = resp.data.get('warnings', [])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'self_invited')

    def test_create_event_unknown_username_warning(self):
        """Unknown usernames are silently dropped; event still created with valid invitees."""
        owner_login = self.api_client.post(
            self.login_url,
            {'username': 'owner', 'password': 'ownerpass'},
            format='json'
        )
        owner_token = owner_login.json()['token']
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {owner_token}')

        event_data = {
            'event_name': 'Unknown Invite Test',
            'proposed_dates': [self.today.strftime('%Y-%m-%d')],
            'invitees': ['invitee1', 'ghost_user', 'nobody'],
        }

        resp = self.api_client.post(self.create_event_url, event_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        event = Event.objects.get(id=resp.data['event_id'])
        # Only invitee1 resolved; the other two do not exist
        self.assertEqual(event.invites.count(), 1)
        self.assertEqual(event.invites.first().invitee.username, 'invitee1')

        # Response must contain an unknown_usernames warning listing both bad names
        warnings = resp.data.get('warnings', [])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'unknown_usernames')
        self.assertIn('ghost_user', warnings[0]['message'])
        self.assertIn('nobody', warnings[0]['message'])

    def test_create_event_both_warnings(self):
        """Both self-invite and unknown usernames produce two warnings; valid invitees still work."""
        owner_login = self.api_client.post(
            self.login_url,
            {'username': 'owner', 'password': 'ownerpass'},
            format='json'
        )
        owner_token = owner_login.json()['token']
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {owner_token}')

        event_data = {
            'event_name': 'Both Warnings Test',
            'proposed_dates': [self.today.strftime('%Y-%m-%d')],
            'invitees': ['owner', 'invitee2', 'phantom'],
        }

        resp = self.api_client.post(self.create_event_url, event_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        event = Event.objects.get(id=resp.data['event_id'])
        # Only invitee2 should have an invite
        self.assertEqual(event.invites.count(), 1)
        self.assertEqual(event.invites.first().invitee.username, 'invitee2')

        warnings = resp.data.get('warnings', [])
        warning_types = {w['type'] for w in warnings}
        self.assertIn('unknown_usernames', warning_types)
        self.assertIn('self_invited', warning_types)
