"""The statuses the API reports, as constants to compare with.

The models keep a status as the plain string the API sent, so a status a future API
version adds reads fine; these enums are strings, so `message.status ==
MessageStatus.DELIVERED` works.
"""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    """A string enum whose str() and format() are its value, on every Python version (enum.StrEnum is 3.11+)."""

    def __str__(self) -> str:
        return str.__str__(self)


class MessageStatus(_StrEnum):
    """The statuses of a message."""

    SCHEDULED = "scheduled"
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    UNDELIVERED = "undelivered"
    FAILED = "failed"
    CANCELED = "canceled"


class VerificationStatus(_StrEnum):
    """The statuses of a verification."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"


class AccountStatus(_StrEnum):
    """The statuses of an account."""

    ACTIVE = "active"
    PENDING = "pending"
    DISABLED = "disabled"


class DeliveryStatus(_StrEnum):
    """The statuses a delivery status callback reports."""

    SENT = "sent"
    DELIVERED = "delivered"
    UNDELIVERED = "undelivered"
