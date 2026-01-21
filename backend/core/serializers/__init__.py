"""
Serializers package for the Calendar API.
"""
from core.serializers.auth import UserRegistrationSerializer, LoginSerializer
from core.serializers.event import (
    EventSerializer,
    EventCreateSerializer,
    EventConfirmSerializer,
    EventUpdateSerializer,
    ProposedDateSerializer,
    ProposedDateCreateSerializer,
)
from core.serializers.event_invite import (
    EventInviteSerializer,
    EventInviteCreateSerializer,
    InviteStatusUpdateSerializer,
)
from core.serializers.vote import VoteCreateSerializer, DateVoteSerializer

__all__ = [
    # Auth
    'UserRegistrationSerializer',
    'LoginSerializer',
    # Event
    'EventSerializer',
    'EventCreateSerializer',
    'EventConfirmSerializer',
    'EventUpdateSerializer',
    'ProposedDateSerializer',
    'ProposedDateCreateSerializer',
    # Event Invite
    'EventInviteSerializer',
    'EventInviteCreateSerializer',
    'InviteStatusUpdateSerializer',
    # Vote
    'VoteCreateSerializer',
    'DateVoteSerializer',
]
