"""
Tests for model functionality.
"""
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Event, EventInvite, ProposedDate, DateVote


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
            user=self.user
        )
        self.assertEqual(event.event_name, 'Test Event')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.status, Event.Status.PROPOSED)
        self.assertIsNone(event.confirmed_date)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)
    
    def test_event_status_choices(self):
        """Test all status choices are valid."""
        for status_choice in Event.Status.choices:
            event = Event.objects.create(
                event_name=f'Event {status_choice[0]}',
                user=self.user,
                status=status_choice[0]
            )
            self.assertEqual(event.status, status_choice[0])
    
    def test_event_ordering(self):
        """Test events are ordered by created_at descending."""
        event1 = Event.objects.create(event_name='Event 1', user=self.user)
        event2 = Event.objects.create(event_name='Event 2', user=self.user)
        event3 = Event.objects.create(event_name='Event 3', user=self.user)
        
        events = list(Event.objects.all())
        self.assertEqual(events[0], event3)
        self.assertEqual(events[1], event2)
        self.assertEqual(events[2], event1)
    
    def test_event_with_confirmed_date(self):
        """Test event with confirmed date."""
        event = Event.objects.create(
            event_name='Test Event',
            user=self.user
        )
        proposed_date = ProposedDate.objects.create(
            event=event,
            date=self.today
        )
        
        event.status = Event.Status.CONFIRMED
        event.confirmed_date = proposed_date
        event.save()
        
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CONFIRMED)
        self.assertEqual(event.confirmed_date, proposed_date)


class ProposedDateModelTests(TestCase):
    """Test ProposedDate model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.user
        )
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
    
    def test_proposed_date_creation(self):
        """Test creating a ProposedDate instance."""
        proposed_date = ProposedDate.objects.create(
            event=self.event,
            date=self.today
        )
        self.assertEqual(proposed_date.event, self.event)
        self.assertEqual(proposed_date.date, self.today)
        self.assertIsNotNone(proposed_date.created_at)
    
    def test_proposed_date_unique_together(self):
        """Test that duplicate proposed dates are not allowed."""
        ProposedDate.objects.create(event=self.event, date=self.today)
        
        with self.assertRaises(Exception):
            ProposedDate.objects.create(event=self.event, date=self.today)
    
    def test_proposed_date_ordering(self):
        """Test proposed dates are ordered by date."""
        date3 = ProposedDate.objects.create(
            event=self.event,
            date=self.today + timedelta(days=2)
        )
        date1 = ProposedDate.objects.create(
            event=self.event,
            date=self.today
        )
        date2 = ProposedDate.objects.create(
            event=self.event,
            date=self.tomorrow
        )
        
        dates = list(self.event.proposed_dates.all())
        self.assertEqual(dates[0], date1)
        self.assertEqual(dates[1], date2)
        self.assertEqual(dates[2], date3)
    
    def test_proposed_date_cascade_delete(self):
        """Test that proposed dates are deleted when event is deleted."""
        proposed_date = ProposedDate.objects.create(
            event=self.event,
            date=self.today
        )
        proposed_date_id = proposed_date.id
        
        self.event.delete()
        
        self.assertFalse(ProposedDate.objects.filter(id=proposed_date_id).exists())


class DateVoteModelTests(TestCase):
    """Test DateVote model functionality."""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            password='testpass123'
        )
        self.voter = User.objects.create_user(
            username='voter',
            password='testpass123'
        )
        self.event = Event.objects.create(
            event_name='Test Event',
            user=self.owner
        )
        self.proposed_date = ProposedDate.objects.create(
            event=self.event,
            date=datetime.now().date()
        )
    
    def test_date_vote_creation(self):
        """Test creating a DateVote instance."""
        vote = DateVote.objects.create(
            proposed_date=self.proposed_date,
            user=self.voter,
            availability=DateVote.Availability.AVAILABLE
        )
        self.assertEqual(vote.proposed_date, self.proposed_date)
        self.assertEqual(vote.user, self.voter)
        self.assertEqual(vote.availability, DateVote.Availability.AVAILABLE)
        self.assertIsNotNone(vote.created_at)
        self.assertIsNotNone(vote.updated_at)
    
    def test_date_vote_unique_together(self):
        """Test that duplicate votes are not allowed."""
        DateVote.objects.create(
            proposed_date=self.proposed_date,
            user=self.voter,
            availability=DateVote.Availability.AVAILABLE
        )
        
        with self.assertRaises(Exception):
            DateVote.objects.create(
                proposed_date=self.proposed_date,
                user=self.voter,
                availability=DateVote.Availability.MAYBE
            )
    
    def test_date_vote_availability_choices(self):
        """Test all availability choices are valid."""
        for i, choice in enumerate(DateVote.Availability.choices):
            voter = User.objects.create_user(
                username=f'voter_{i}',
                password='testpass123'
            )
            vote = DateVote.objects.create(
                proposed_date=self.proposed_date,
                user=voter,
                availability=choice[0]
            )
            self.assertEqual(vote.availability, choice[0])
    
    def test_date_vote_cascade_delete_on_proposed_date(self):
        """Test that votes are deleted when proposed date is deleted."""
        vote = DateVote.objects.create(
            proposed_date=self.proposed_date,
            user=self.voter,
            availability=DateVote.Availability.AVAILABLE
        )
        vote_id = vote.id
        
        self.proposed_date.delete()
        
        self.assertFalse(DateVote.objects.filter(id=vote_id).exists())
    
    def test_date_vote_cascade_delete_on_user(self):
        """Test that votes are deleted when user is deleted."""
        vote = DateVote.objects.create(
            proposed_date=self.proposed_date,
            user=self.voter,
            availability=DateVote.Availability.AVAILABLE
        )
        vote_id = vote.id
        
        self.voter.delete()
        
        self.assertFalse(DateVote.objects.filter(id=vote_id).exists())


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
    
    def test_event_invite_creation(self):
        """Test creating an EventInvite instance."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        self.assertEqual(invite.event, self.event)
        self.assertEqual(invite.owner, self.owner)
        self.assertEqual(invite.invitee, self.invitee)
        self.assertEqual(invite.status, EventInvite.Status.PENDING)
        self.assertIsNotNone(invite.created_at)
        self.assertIsNotNone(invite.updated_at)
    
    def test_event_invite_unique_together(self):
        """Test that duplicate invites are not allowed."""
        EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        
        with self.assertRaises(Exception):
            EventInvite.objects.create(
                event=self.event,
                owner=self.owner,
                invitee=self.invitee
            )
    
    def test_event_invite_status_choices(self):
        """Test all status choices are valid."""
        for i, choice in enumerate(EventInvite.Status.choices):
            invitee = User.objects.create_user(
                username=f'invitee_{i}',
                password='testpass123'
            )
            invite = EventInvite.objects.create(
                event=self.event,
                owner=self.owner,
                invitee=invitee,
                status=choice[0]
            )
            self.assertEqual(invite.status, choice[0])
    
    def test_event_invite_cascade_delete(self):
        """Test that invites are deleted when event is deleted."""
        invite = EventInvite.objects.create(
            event=self.event,
            owner=self.owner,
            invitee=self.invitee
        )
        invite_id = invite.id
        
        self.event.delete()
        
        self.assertFalse(EventInvite.objects.filter(id=invite_id).exists())
