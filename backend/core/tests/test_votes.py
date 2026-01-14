"""
Basic tests for vote-related views.
"""
from datetime import datetime
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status

from core.models import Event, ProposedDate, DateVote, EventInvite


class VoteEndpointTests(APITestCase):
    """Basic tests for voting and vote retrieval endpoints."""

    def setUp(self):
        # Users
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.invitee = User.objects.create_user(username='invitee', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')

        # Tokens
        self.owner_token, _ = Token.objects.get_or_create(user=self.owner)
        self.invitee_token, _ = Token.objects.get_or_create(user=self.invitee)

        # Event with one proposed date
        self.event = Event.objects.create(event_name='Vote Event', user=self.owner)
        self.proposed_date = ProposedDate.objects.create(event=self.event, date=datetime.now().date())

        # Invite invitee
        EventInvite.objects.create(event=self.event, owner=self.owner, invitee=self.invitee)

        self.client = APIClient()

    def test_vote_success(self):
        """An invited user can post a vote successfully."""
        url = reverse('votes:vote', args=[self.event.id, self.proposed_date.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')

        payload = {'availability': 'AVAILABLE'}
        resp = self.client.post(url, payload, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(DateVote.objects.count(), 1)
        vote = DateVote.objects.first()
        self.assertEqual(vote.availability, 'AVAILABLE')
        self.assertEqual(vote.user, self.invitee)

        # Response should include user id and availability
        self.assertEqual(resp.data.get('availability'), 'AVAILABLE')
        self.assertEqual(resp.data.get('user'), self.invitee.id)

    def test_vote_unauthorized(self):
        """Posting without token is unauthorized."""
        url = reverse('votes:vote', args=[self.event.id, self.proposed_date.id])
        resp = self.client.post(url, {'availability': 'AVAILABLE'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vote_invalid_availability(self):
        """Invalid availability values return 400."""
        url = reverse('votes:vote', args=[self.event.id, self.proposed_date.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        resp = self.client.post(url, {'availability': 'BAD'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_event_votes(self):
        """Owner can retrieve votes summary for an event."""
        # create a vote from invitee and owner
        DateVote.objects.create(proposed_date=self.proposed_date, user=self.invitee, availability='AVAILABLE')
        DateVote.objects.create(proposed_date=self.proposed_date, user=self.owner, availability='MAYBE')

        url = reverse('votes:list', args=[self.event.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.owner_token.key}')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        # There should be one entry for the proposed date
        self.assertEqual(len(resp.data), 1)
        summary = resp.data[0].get('summary', {})
        self.assertEqual(summary.get('available'), 1)
        self.assertEqual(summary.get('maybe'), 1)
        self.assertEqual(summary.get('total'), 2)

    def test_get_my_votes(self):
        """A user can get their own votes for an event."""
        DateVote.objects.create(proposed_date=self.proposed_date, user=self.invitee, availability='AVAILABLE')

        url = reverse('votes:my_votes', args=[self.event.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Should return a list with one vote
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0].get('availability'), 'AVAILABLE')

    def test_delete_vote(self):
        """A user can delete their vote."""
        vote = DateVote.objects.create(proposed_date=self.proposed_date, user=self.invitee, availability='AVAILABLE')

        url = reverse('votes:delete', args=[self.event.id, self.proposed_date.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.invitee_token.key}')
        resp = self.client.delete(url)

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DateVote.objects.filter(id=vote.id).exists())
