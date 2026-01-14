from django.db import models


class Event(models.Model):
    """
    Event model representing an event proposal.
    Events start as PROPOSED and can be CONFIRMED or CANCELLED.
    """
    
    class Status(models.TextChoices):
        PROPOSED = 'PROPOSED', 'Proposed'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    event_name = models.CharField(max_length=255)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='events')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PROPOSED
    )
    confirmed_date = models.ForeignKey(
        'ProposedDate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'


class ProposedDate(models.Model):
    """
    Model representing a proposed date for an event.
    Invitees can vote on their availability for each proposed date.
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='proposed_dates'
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
        verbose_name = 'Proposed Date'
        verbose_name_plural = 'Proposed Dates'
        unique_together = ['event', 'date']


class DateVote(models.Model):
    """
    Model representing a user's vote on their availability for a proposed date.
    """
    
    class Availability(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        MAYBE = 'MAYBE', 'Maybe'
        NOT_AVAILABLE = 'NOT_AVAILABLE', 'Not Available'
    
    proposed_date = models.ForeignKey(
        ProposedDate,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='date_votes'
    )
    availability = models.CharField(
        max_length=15,
        choices=Availability.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Date Vote'
        verbose_name_plural = 'Date Votes'
        unique_together = ['proposed_date', 'user']


class EventInvite(models.Model):
    """Model for event invitations."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
        MAYBE = 'MAYBE', 'Maybe'
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invites')
    owner = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='sent_invites'
    )
    invitee = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='received_invites'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Event Invite'
        verbose_name_plural = 'Event Invites'
        unique_together = ['event', 'invitee']
