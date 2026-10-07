from __future__ import annotations

import json

import pytest

from calisero import DeliveryStatus, DeliveryWebhookMessage, InvalidWebhookPayloadError
from tests.support.fixtures import PHONE, webhook_payload, without


class TestFromJson:
    def test_reads_a_full_payload(self) -> None:
        message = DeliveryWebhookMessage.from_json(json.dumps(webhook_payload()))

        assert message == DeliveryWebhookMessage(
            message_id="019961db-14a7-7348-963f-5a7a789a969f",
            sender="CALISERO",
            recipient=PHONE,
            status="delivered",
            schedule_at="2025-09-19T12:02:51.000000Z",
            sent_at="2025-09-19T12:01:15.000000Z",
            delivered_at="2025-09-19T12:02:53.000000Z",
            price=0.0378,
            remaining_balance=999.392,
            daily_limit=1000,
            daily_remaining=588,
            sent_today=412,
        )
        assert message.status == DeliveryStatus.DELIVERED

    def test_reads_a_raw_body_given_as_bytes(self) -> None:
        raw = json.dumps(webhook_payload(recipient="+40742***351")).encode()

        assert DeliveryWebhookMessage.from_json(raw).recipient == "+40742***351"
        assert DeliveryWebhookMessage.from_json(bytearray(raw)).recipient == "+40742***351"
        assert DeliveryWebhookMessage.from_json(memoryview(raw)).recipient == "+40742***351"

    def test_refuses_a_body_that_is_not_json(self) -> None:
        with pytest.raises(InvalidWebhookPayloadError, match=r"^Invalid delivery webhook payload: ") as caught:
            DeliveryWebhookMessage.from_json("{not json")

        assert isinstance(caught.value.__cause__, json.JSONDecodeError)

    def test_refuses_a_body_that_is_not_utf8(self) -> None:
        with pytest.raises(InvalidWebhookPayloadError, match=r"^Invalid delivery webhook payload: "):
            DeliveryWebhookMessage.from_json(b'{"messageId": "\xff"}')

    def test_refuses_a_body_nested_too_deeply(self) -> None:
        with pytest.raises(InvalidWebhookPayloadError, match="nests too deeply"):
            DeliveryWebhookMessage.from_json("[" * 100_000)

    def test_refuses_json_that_is_not_an_object_like_the_list_sent_for_a_cancelled_message(self) -> None:
        with pytest.raises(
            InvalidWebhookPayloadError,
            match=r"^Invalid delivery webhook payload: expected an object, got an array\.$",
        ):
            DeliveryWebhookMessage.from_json("[]")

        with pytest.raises(InvalidWebhookPayloadError, match="got null"):
            DeliveryWebhookMessage.from_json("null")


class TestFromDict:
    def test_reads_a_minimal_payload(self) -> None:
        message = DeliveryWebhookMessage.from_dict(
            {"messageId": "019961db-14a7-7348-963f-5a7a789a969f", "recipient": PHONE, "status": "sent", "price": 0.0378}
        )

        assert message.status == DeliveryStatus.SENT
        assert (
            message.sender,
            message.schedule_at,
            message.sent_at,
            message.delivered_at,
            message.remaining_balance,
            message.daily_limit,
            message.daily_remaining,
            message.sent_today,
        ) == (None, None, None, None, None, None, None, None)

    def test_reads_a_payload_of_a_message_sent_with_the_default_sender(self) -> None:
        assert DeliveryWebhookMessage.from_dict(webhook_payload(sender=None)).sender is None

    def test_reads_a_payload_that_predates_the_daily_limit(self) -> None:
        message = DeliveryWebhookMessage.from_dict(
            without(webhook_payload(), "dailyLimit", "dailyRemaining", "sentToday")
        )

        assert (message.daily_limit, message.daily_remaining, message.sent_today) == (None, None, None)

    def test_reads_an_account_without_a_daily_limit(self) -> None:
        message = DeliveryWebhookMessage.from_dict(webhook_payload(dailyLimit=None, dailyRemaining=None))

        assert message.daily_limit is None
        assert message.sent_today == 412

    def test_reads_amounts_sent_as_strings(self) -> None:
        message = DeliveryWebhookMessage.from_dict(webhook_payload(price="0.0378", remainingBalance="12.5"))

        assert (message.price, message.remaining_balance) == (0.0378, 12.5)

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"messageId": None}, '"messageId" must be a non-empty string, got null'),
            ({"messageId": ""}, '"messageId" must be a non-empty string, got a string'),
            ({"recipient": 42}, '"recipient" must be a non-empty string, got a number'),
            ({"status": None}, '"status" must be a non-empty string, got null'),
            ({"price": "free"}, '"price" must be a number, got a string'),
            ({"price": False}, '"price" must be a number, got a boolean'),
        ],
    )
    def test_refuses_a_payload_with_a_malformed_field(self, overrides: dict[str, object], message: str) -> None:
        with pytest.raises(InvalidWebhookPayloadError) as caught:
            DeliveryWebhookMessage.from_dict(webhook_payload(**overrides))

        assert str(caught.value) == f"Invalid delivery webhook payload: {message}."

    @pytest.mark.parametrize("field", ["messageId", "recipient", "status", "price"])
    def test_refuses_a_payload_without_a_required_field(self, field: str) -> None:
        with pytest.raises(InvalidWebhookPayloadError, match=f'"{field}" must be .*, got nothing'):
            DeliveryWebhookMessage.from_dict(without(webhook_payload(), field))

    def test_ignores_daily_counts_that_are_not_integers(self) -> None:
        message = DeliveryWebhookMessage.from_dict(webhook_payload(dailyLimit=10.5, sentToday="3"))

        assert (message.daily_limit, message.sent_today) == (None, None)
