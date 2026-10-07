from __future__ import annotations

import dataclasses

import pytest

from calisero import Message, MessageStatus, ShortenedLink
from tests.support.fixtures import MESSAGE_ID, PHONE, message_data, shortened_link_data, without


def test_reads_a_message_with_every_field() -> None:
    message = Message.from_dict(
        message_data(
            status="delivered",
            sent_at="2025-02-06T10:18:45.000000Z",
            delivered_at="2025-02-06T10:18:50.000000Z",
            shortened_urls=[shortened_link_data()],
        )
    )

    assert message == Message(
        id=MESSAGE_ID,
        recipient=PHONE,
        body="Hello from Calisero!",
        parts=1,
        created_at="2025-02-06T10:18:43.000000Z",
        scheduled_at="2025-02-06T10:18:43.000000Z",
        sent_at="2025-02-06T10:18:45.000000Z",
        delivered_at="2025-02-06T10:18:50.000000Z",
        callback_url="https://yourapp.com/webhooks/calisero",
        status="delivered",
        sender="CALISERO",
        shortened_urls=(
            ShortenedLink(
                id="019adfbb-40a1-71ee-bcb5-8d551b8cfdae",
                original_link="https://yourstore.com/orders/12345/tracking",
                shortened_link="https://calisero.ro/s/ghJKPV",
                click_count=3,
                last_click="2025-12-02T16:01:12.000000Z",
                created_at="2025-12-02T15:43:02.000000Z",
            ),
        ),
    )


def test_reads_a_minimal_message() -> None:
    data = without(
        message_data(), "scheduled_at", "sent_at", "delivered_at", "callback_url", "sender", "shortened_urls"
    )

    message = Message.from_dict(data)

    assert (message.scheduled_at, message.sent_at, message.delivered_at, message.callback_url, message.sender) == (
        None,
        None,
        None,
        None,
        None,
    )
    assert message.shortened_urls == ()


def test_reads_a_link_never_clicked() -> None:
    link = ShortenedLink.from_dict(shortened_link_data(click_count=None, last_click=None))

    assert (link.click_count, link.last_click) == (0, None)


def test_reads_shortened_urls_that_are_not_a_list_as_none() -> None:
    assert Message.from_dict(message_data(shortened_urls=None)).shortened_urls == ()


def test_reads_the_parts_written_as_a_whole_float() -> None:
    assert Message.from_dict(message_data(parts=2.0)).parts == 2


def test_compares_the_status_with_the_constants() -> None:
    message = Message.from_dict(message_data(status="delivered"))

    assert message.status == MessageStatus.DELIVERED
    assert message.status != MessageStatus.UNDELIVERED
    assert str(MessageStatus.DELIVERED) == "delivered"
    assert f"{MessageStatus.CANCELED}" == "canceled"


def test_reads_a_status_a_future_api_version_adds() -> None:
    assert Message.from_dict(message_data(status="expired")).status == "expired"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (without(message_data(), "id"), 'Invalid message: "id" must be a string, got nothing.'),
        (message_data(parts="two"), 'Invalid message: "parts" must be an integer, got a string.'),
        (message_data(parts=1.5), 'Invalid message: "parts" must be an integer, got a number.'),
        (message_data(parts=True), 'Invalid message: "parts" must be an integer, got a boolean.'),
        (message_data(status=None), 'Invalid message: "status" must be a string, got null.'),
        (
            message_data(shortened_urls=[shortened_link_data(original_link=None)]),
            'Invalid message.shortened_urls[0]: "original_link" must be a string, got null.',
        ),
        ([], "Invalid message: expected an object, got an array."),
        ("message", "Invalid message: expected an object, got a string."),
    ],
)
def test_refuses_a_malformed_message_naming_the_field_at_fault(data: object, message: str) -> None:
    with pytest.raises(TypeError) as caught:
        Message.from_dict(data)

    assert str(caught.value) == message


def test_names_the_context_it_is_given() -> None:
    with pytest.raises(TypeError, match=r'^Invalid page\.data\[3\]: "id" must be a string, got nothing\.$'):
        Message.from_dict({}, "page.data[3]")


def test_is_immutable() -> None:
    message = Message.from_dict(message_data())

    with pytest.raises(dataclasses.FrozenInstanceError):
        message.status = "delivered"  # type: ignore[misc]
