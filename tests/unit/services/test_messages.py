from __future__ import annotations

from datetime import datetime, timezone

import pytest

from calisero import (
    ApiError,
    ApiResponse,
    DailyLimitExceededError,
    ForbiddenError,
    Message,
    NotFoundError,
    Paginated,
    ResponseMeta,
    ValidationError,
)
from tests.support.fixtures import (
    DAILY_LIMIT_BODY,
    MESSAGE_ID,
    PHONE,
    TRACE_ID,
    message_data,
    page_of,
    shortened_link_data,
)
from tests.support.stub_transport import client_answering, json_response, request_body

BASE = "https://rest.calisero.ro/api/v1"


class TestCreate:
    def test_sends_a_message_with_every_option(self) -> None:
        client, transport = client_answering(json_response(201, {"data": message_data()}))

        client.messages.create(
            recipient=PHONE,
            body="Your code is 123456",
            visible_body="Your code is ******",
            validity=24,
            schedule_at=datetime(2026, 12, 25, 8, tzinfo=timezone.utc),
            callback_url="https://yourapp.com/webhooks/calisero",
            sender="Calisero",
            shorten_urls=True,
        )

        assert transport.last_request.method == "POST"
        assert transport.last_request.url == f"{BASE}/messages"
        assert request_body(transport.last_request) == {
            "recipient": PHONE,
            "body": "Your code is 123456",
            "visible_body": "Your code is ******",
            "validity": 24,
            "schedule_at": "2026-12-25 10:00:00",
            "callback_url": "https://yourapp.com/webhooks/calisero",
            "sender": "Calisero",
            "shorten_urls": True,
        }

    def test_sends_a_minimal_message_and_reads_the_answer(self) -> None:
        client, transport = client_answering(json_response(201, {"data": message_data()}))

        response = client.messages.create(recipient=PHONE, body="Hello from Calisero!")

        assert request_body(transport.last_request) == {"recipient": PHONE, "body": "Hello from Calisero!"}
        assert isinstance(response, ApiResponse)
        assert response.data == Message.from_dict(message_data())

    def test_sends_a_schedule_already_in_romania_time_as_is(self) -> None:
        client, transport = client_answering(json_response(201, {"data": message_data()}))

        client.messages.create(recipient=PHONE, body="Hello!", schedule_at="2026-12-25 10:00:00")

        assert request_body(transport.last_request) == {
            "recipient": PHONE,
            "body": "Hello!",
            "schedule_at": "2026-12-25 10:00:00",
        }

    def test_refuses_a_naive_schedule_before_sending(self) -> None:
        client, transport = client_answering()

        with pytest.raises(ValueError, match="timezone-aware"):
            client.messages.create(recipient=PHONE, body="Hello!", schedule_at=datetime(2026, 12, 25, 10))

        assert transport.requests == []

    def test_reads_the_shortened_links(self) -> None:
        client, _ = client_answering(json_response(201, {"data": message_data(shortened_urls=[shortened_link_data()])}))

        response = client.messages.create(
            recipient=PHONE, body="Track it: https://yourstore.com/orders/12345/tracking", shorten_urls=True
        )

        [link] = response.data.shortened_urls
        assert (link.original_link, link.shortened_link) == (
            "https://yourstore.com/orders/12345/tracking",
            "https://calisero.ro/s/ghJKPV",
        )

    def test_reads_what_is_left_of_the_daily_limit(self) -> None:
        headers = {
            "X-Trace-Id": TRACE_ID,
            "X-RateLimit-Limit": "240",
            "X-RateLimit-Remaining": "239",
            "X-Daily-Limit": "1000",
            "X-Daily-Remaining": "872",
        }
        client, _ = client_answering(json_response(201, {"data": message_data()}, headers))

        response = client.messages.create(recipient=PHONE, body="Hello!")

        assert response.response_meta == ResponseMeta(
            trace_id=TRACE_ID, rate_limit_limit=240, rate_limit_remaining=239, daily_limit=1000, daily_remaining=872
        )

    def test_raises_the_daily_limit_refusal(self) -> None:
        client, _ = client_answering(json_response(429, DAILY_LIMIT_BODY, {"Retry-After": "21600"}))

        with pytest.raises(DailyLimitExceededError) as caught:
            client.messages.create(recipient=PHONE, body="Hello!")

        assert (caught.value.daily_remaining, caught.value.retry_after) == (0, 21600)

    def test_raises_the_refusal_of_an_opted_out_recipient(self) -> None:
        body = {
            "message": "The recipient has opted out of receiving messages.",
            "errors": {"recipient": ["The recipient has opted out of receiving messages."]},
        }
        client, _ = client_answering(json_response(422, body))

        with pytest.raises(ValidationError) as caught:
            client.messages.create(recipient=PHONE, body="Special offer!")

        assert caught.value.validation_errors == {"recipient": ["The recipient has opted out of receiving messages."]}

    def test_passes_its_timeout(self) -> None:
        client, transport = client_answering(json_response(201, {"data": message_data()}))

        client.messages.create(recipient=PHONE, body="Hello!", timeout=3)

        assert transport.last_request.timeout == 3


class TestGet:
    def test_retrieves_a_message(self) -> None:
        client, transport = client_answering(json_response(200, {"data": message_data(status="delivered")}))

        response = client.messages.get(MESSAGE_ID)

        assert (transport.last_request.method, transport.last_request.url) == ("GET", f"{BASE}/messages/{MESSAGE_ID}")
        assert transport.last_request.body is None
        assert response.data.status == "delivered"

    def test_encodes_the_id(self) -> None:
        client, transport = client_answering(json_response(200, {"data": message_data()}))

        client.messages.get("a/b c?d")

        assert transport.last_request.url == f"{BASE}/messages/a%2Fb%20c%3Fd"

    @pytest.mark.parametrize(("message_id", "error"), [("", ValueError), ("  ", ValueError), (None, TypeError)])
    def test_refuses_an_empty_id_before_sending(self, message_id: object, error: type[Exception]) -> None:
        client, transport = client_answering()

        with pytest.raises(error, match=r"^The message id must be a non-empty string\.$"):
            client.messages.get(message_id)  # type: ignore[arg-type]

        assert transport.requests == []

    def test_raises_not_found(self) -> None:
        client, _ = client_answering(json_response(404, {"message": "Resource not found!", "trace_id": TRACE_ID}))

        with pytest.raises(NotFoundError, match="Resource not found!"):
            client.messages.get(MESSAGE_ID)

    def test_turns_an_unexpected_answer_into_an_api_error(self) -> None:
        client, _ = client_answering(json_response(200, {"message": "OK"}, {"X-Trace-Id": TRACE_ID}))

        with pytest.raises(ApiError) as caught:
            client.messages.get(MESSAGE_ID)

        error = caught.value
        assert type(error) is ApiError
        assert (
            error.message == 'Unexpected API response: Invalid message answer: "data" must be an object, got nothing.'
        )
        assert (error.status_code, error.trace_id, error.error_details) == (200, TRACE_ID, {"message": "OK"})
        assert isinstance(error.__cause__, TypeError)

    def test_names_the_field_of_a_malformed_message(self) -> None:
        client, _ = client_answering(json_response(200, {"data": message_data(parts="one")}))

        with pytest.raises(ApiError, match=r'Invalid message: "parts" must be an integer, got a string\.$'):
            client.messages.get(MESSAGE_ID)

    def test_turns_an_empty_answer_into_an_api_error(self) -> None:
        client, _ = client_answering(json_response(200))

        with pytest.raises(ApiError, match=r"Invalid message answer: expected an object, got null\.$") as caught:
            client.messages.get(MESSAGE_ID)

        assert caught.value.error_details == {}


class TestList:
    def test_lists_the_first_page_without_a_query(self) -> None:
        client, transport = client_answering(json_response(200, page_of([message_data()], "messages")))

        page = client.messages.list()

        assert transport.last_request.url == f"{BASE}/messages"
        assert isinstance(page, Paginated)
        assert [message.id for message in page] == [MESSAGE_ID]
        assert not page.has_next_page

    def test_lists_the_page_it_is_asked_for(self) -> None:
        client, transport = client_answering(
            json_response(200, page_of([message_data()], "messages")),
            json_response(200, page_of([message_data()], "messages", 2, True), {"X-Trace-Id": TRACE_ID}),
        )

        client.messages.list(page=1)
        page = client.messages.list(page=2)

        assert [request.url for request in transport.requests] == [f"{BASE}/messages", f"{BASE}/messages?page=2"]
        assert (page.meta.current_page, page.has_next_page, page.response_meta.trace_id) == (2, True, TRACE_ID)

    @pytest.mark.parametrize(
        ("page", "error"), [(0, ValueError), (-1, ValueError), ("2", TypeError), (True, TypeError)]
    )
    def test_refuses_a_page_that_is_not_a_positive_integer(self, page: object, error: type[Exception]) -> None:
        client, transport = client_answering()

        with pytest.raises(error, match=r"^The page must be a positive integer, got "):
            client.messages.list(page=page)  # type: ignore[arg-type]

        assert transport.requests == []

    def test_names_the_item_of_a_malformed_page(self) -> None:
        client, _ = client_answering(json_response(200, page_of([message_data(), {"id": 42}], "messages")))

        with pytest.raises(ApiError, match=r'Invalid page\.data\[1\]: "id" must be a string, got a number\.$'):
            client.messages.list()


class TestDelete:
    def test_cancels_a_scheduled_message(self) -> None:
        client, transport = client_answering(json_response(200, []))

        client.messages.delete(MESSAGE_ID)

        assert (transport.last_request.method, transport.last_request.url) == (
            "DELETE",
            f"{BASE}/messages/{MESSAGE_ID}",
        )
        assert transport.last_request.body is None

    def test_raises_forbidden_for_a_message_already_sent(self) -> None:
        body = {"message": "This action is unauthorized.", "trace_id": TRACE_ID}
        client, _ = client_answering(json_response(403, body))

        with pytest.raises(ForbiddenError, match=r"^This action is unauthorized\.$"):
            client.messages.delete(MESSAGE_ID)
