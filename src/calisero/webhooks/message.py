from __future__ import annotations

from dataclasses import dataclass

from calisero._internal.fields import FieldReader
from calisero._internal.json import loads
from calisero.errors import InvalidWebhookPayloadError


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryWebhookMessage:
    """The payload Calisero posts to a message's callback URL when its status changes: sent, delivered or undelivered.

    It reaches your endpoint from outside your application, so it is validated: a
    malformed payload raises an `InvalidWebhookPayloadError`.
    """

    #: The message's id (the payload's messageId).
    message_id: str

    #: The sender ID the message went out under; None for the default sender.
    sender: str | None

    #: The recipient in E.164 format.
    recipient: str

    #: The delivery status: sent, delivered or undelivered; compare it with the `DeliveryStatus` constants.
    status: str

    #: When the message was scheduled to go out, if it was scheduled.
    schedule_at: str | None

    #: When the message was handed to the network (statuses sent and delivered).
    sent_at: str | None

    #: When the handset confirmed delivery (status delivered only).
    delivered_at: str | None

    #: The price charged for the message's parts.
    price: float

    #: The account's balance after billing, if available.
    remaining_balance: float | None

    #: The account's daily sending limit when the callback was sent; None when no daily limit applies.
    daily_limit: int | None

    #: How many messages the account could still send today when the callback was sent; None when no
    #: daily limit applies.
    daily_remaining: int | None

    #: The real messages the account created today, Romania time, when the callback was sent: OTP
    #: codes included, test messages left out, one per message whatever its parts. None in payloads
    #: that predate the daily limit.
    sent_today: int | None

    @classmethod
    def from_json(cls, json: str | bytes | bytearray | memoryview) -> DeliveryWebhookMessage:
        """Read the raw body of a callback request.

        Raises:
            InvalidWebhookPayloadError: when the body is not a JSON object or a required field is
                missing or malformed
        """
        try:
            text = json if isinstance(json, str) else bytes(json).decode("utf-8")
            data = loads(text)
        except ValueError as error:
            raise InvalidWebhookPayloadError(f"Invalid delivery webhook payload: {error}") from error

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: object) -> DeliveryWebhookMessage:
        """Read the decoded body of a callback request (e.g. the JSON a web framework decoded).

        Raises:
            InvalidWebhookPayloadError: when it is not an object or a required field is missing or
                malformed
        """
        read = FieldReader.of(data, "delivery webhook payload", InvalidWebhookPayloadError)

        return cls(
            message_id=read.non_empty_string("messageId"),
            sender=read.optional_string("sender"),
            recipient=read.non_empty_string("recipient"),
            status=read.non_empty_string("status"),
            schedule_at=read.optional_string("scheduleAt"),
            sent_at=read.optional_string("sentAt"),
            delivered_at=read.optional_string("deliveredAt"),
            price=read.number("price"),
            remaining_balance=read.optional_number("remainingBalance"),
            daily_limit=read.optional_integer("dailyLimit"),
            daily_remaining=read.optional_integer("dailyRemaining"),
            sent_today=read.optional_integer("sentToday"),
        )
