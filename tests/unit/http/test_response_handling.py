from __future__ import annotations

import pytest

from calisero import (
    ApiError,
    DailyLimitExceededError,
    ForbiddenError,
    HttpResponse,
    NotFoundError,
    RateLimitedError,
    ServerError,
    TransportError,
    UnauthorizedError,
    ValidationError,
)
from tests.support.fixtures import DAILY_LIMIT_BODY, TRACE_ID
from tests.support.stub_transport import StubAnswer, http_client_answering, json_response


def error_for(answer: StubAnswer) -> ApiError:
    """The error a GET answered with `answer` raises."""
    http_client, _ = http_client_answering(answer)

    with pytest.raises(ApiError) as caught:
        http_client.get("/messages")

    return caught.value


class TestErrorAnswers:
    def test_takes_the_message_and_the_trace_id_from_the_error_body(self) -> None:
        error = error_for(json_response(404, {"message": "Resource not found!", "trace_id": TRACE_ID}))

        assert isinstance(error, NotFoundError)
        assert error.message == "Resource not found!"
        assert str(error) == "Resource not found!"
        assert error.status_code == 404
        assert error.trace_id == TRACE_ID
        assert error.request_id == TRACE_ID
        assert error.error_details == {"message": "Resource not found!", "trace_id": TRACE_ID}

    @pytest.mark.parametrize("name", ["X-Trace-Id", "x-trace-id", "X-TRACE-ID"])
    def test_reads_the_trace_id_header_whatever_its_spelling_before_the_body(self, name: str) -> None:
        error = error_for(
            json_response(401, {"message": "Unauthenticated.", "trace_id": "from-body"}, {name: TRACE_ID})
        )

        assert isinstance(error, UnauthorizedError)
        assert error.trace_id == TRACE_ID

    def test_still_reads_an_x_request_id_header_without_a_trace_id(self) -> None:
        assert error_for(HttpResponse(404, {"X-Request-ID": "req_123"}, "")).trace_id == "req_123"

    def test_gives_an_error_without_a_json_body_a_generic_message(self) -> None:
        error = error_for(HttpResponse(502, {"Content-Type": "text/html"}, "<html>Bad Gateway</html>"))

        assert isinstance(error, ServerError)
        assert (error.message, error.status_code, error.trace_id, error.error_details) == (
            "HTTP error 502",
            502,
            None,
            {},
        )

    def test_ignores_an_error_body_that_is_json_but_not_an_object(self) -> None:
        error = error_for(HttpResponse(500, {}, '["Server Error"]'))

        assert (error.message, error.error_details) == ("HTTP error 500", {})

    def test_reads_the_message_from_error_message_when_there_is_no_message(self) -> None:
        assert error_for(json_response(400, {"error": {"message": "Bad request body"}})).message == "Bad request body"

    def test_ignores_an_error_message_that_is_not_text(self) -> None:
        assert error_for(json_response(400, {"error": {"message": 42}})).message == "HTTP error 400"

    def test_gives_an_empty_message_a_generic_one(self) -> None:
        error = error_for(json_response(403, {"message": ""}))

        assert isinstance(error, ForbiddenError)
        assert error.message == "HTTP error 403"

    @pytest.mark.parametrize(
        ("status", "error_class"),
        [
            (401, UnauthorizedError),
            (403, ForbiddenError),
            (404, NotFoundError),
            (422, ValidationError),
            (429, RateLimitedError),
            (500, ServerError),
            (502, ServerError),
            (503, ServerError),
            (504, ServerError),
        ],
    )
    def test_maps_the_status_to_its_error_class(self, status: int, error_class: type[ApiError]) -> None:
        error = error_for(json_response(status, {"message": f"Status {status}"}))

        assert type(error) is error_class
        assert error.status_code == status
        assert error.message == f"Status {status}"

    @pytest.mark.parametrize("status", [302, 400, 405, 409, 418, 501])
    def test_maps_another_status_to_a_plain_api_error(self, status: int) -> None:
        error = error_for(json_response(status, {"message": "Refused"}))

        assert type(error) is ApiError
        assert error.status_code == status


class TestValidationErrors:
    def test_reads_the_field_errors(self) -> None:
        error = error_for(
            json_response(
                422,
                {
                    "message": "The recipient field is required. (and 1 more error)",
                    "errors": {
                        "recipient": ["The recipient field is required."],
                        "body": ["The body field is required."],
                    },
                    "trace_id": TRACE_ID,
                },
                {"X-Trace-Id": TRACE_ID},
            )
        )

        assert isinstance(error, ValidationError)
        assert error.message == "The recipient field is required. (and 1 more error)"
        assert error.trace_id == TRACE_ID
        assert error.validation_errors == {
            "recipient": ["The recipient field is required."],
            "body": ["The body field is required."],
        }

    def test_reads_the_duplicate_message_guard(self) -> None:
        error = error_for(
            json_response(
                422,
                {
                    "message": "Duplicate SMS request detected.",
                    "errors": {
                        "duplicate_sms": [
                            "A similar SMS message has been recently submitted. Please wait a moment before trying "
                            "again."
                        ]
                    },
                },
            )
        )

        assert isinstance(error, ValidationError)
        assert list(error.validation_errors) == ["duplicate_sms"]

    def test_reads_validation_errors_when_there_are_no_errors(self) -> None:
        error = error_for(json_response(422, {"message": "Invalid.", "validation_errors": {"code": ["Wrong code."]}}))

        assert isinstance(error, ValidationError)
        assert error.validation_errors == {"code": ["Wrong code."]}

    def test_has_no_field_errors_when_the_body_carries_none(self) -> None:
        # The API's own 422s carry field errors; a body without them must not pass for them
        error = error_for(json_response(422, {"message": "The request could not be processed.", "trace_id": TRACE_ID}))

        assert isinstance(error, ValidationError)
        assert error.validation_errors == {}
        assert error.error_details["trace_id"] == TRACE_ID

    def test_turns_a_single_message_into_a_list_and_drops_what_is_not_text(self) -> None:
        error = error_for(
            json_response(
                422,
                {
                    "message": "Invalid.",
                    "errors": {
                        "phone": "Invalid phone.",
                        "code": ["Wrong.", 42, None],
                        "body": 42,
                        "sender": {"nested": True},
                    },
                },
            )
        )

        assert isinstance(error, ValidationError)
        assert error.validation_errors == {"phone": ["Invalid phone."], "code": ["Wrong."]}


class TestRateLimits:
    def test_reads_a_refusal_of_the_request_rate_limit(self) -> None:
        # Lowercase names, as HTTP/2 sends them
        error = error_for(
            json_response(
                429,
                {"message": "Too Many Attempts.", "trace_id": TRACE_ID},
                {
                    "retry-after": "17",
                    "x-ratelimit-limit": "240",
                    "x-ratelimit-remaining": "0",
                    "x-ratelimit-reset": "1790000000",
                    "x-trace-id": TRACE_ID,
                },
            )
        )

        assert type(error) is RateLimitedError
        assert (error.message, error.status_code, error.trace_id) == ("Too Many Attempts.", 429, TRACE_ID)
        assert (error.retry_after, error.rate_limit_limit, error.rate_limit_remaining, error.rate_limit_reset) == (
            17,
            240,
            0,
            1790000000,
        )

    def test_reads_a_refusal_of_the_daily_sending_limit(self) -> None:
        # Mixed-case names, as HTTP/1.1 sends them
        error = error_for(
            json_response(
                429,
                DAILY_LIMIT_BODY,
                {
                    "Retry-After": "21600",
                    "X-Daily-Limit": "1000",
                    "X-Daily-Remaining": "0",
                    "X-RateLimit-Limit": "240",
                    "X-RateLimit-Remaining": "238",
                    "X-Trace-Id": TRACE_ID,
                },
            )
        )

        # Code written against RateLimitedError keeps catching it
        assert isinstance(error, RateLimitedError)
        assert isinstance(error, DailyLimitExceededError)
        assert (error.message, error.status_code, error.trace_id) == (DAILY_LIMIT_BODY["message"], 429, TRACE_ID)
        assert (error.daily_limit, error.daily_remaining, error.resets_at) == (1000, 0, "2026-10-01T00:00:00+03:00")
        assert (error.retry_after, error.rate_limit_limit, error.rate_limit_remaining, error.rate_limit_reset) == (
            21600,
            240,
            238,
            None,
        )
        assert error.error_details["code"] == "daily_limit_exceeded"

    def test_falls_back_to_the_headers_for_what_the_daily_limit_body_lacks(self) -> None:
        error = error_for(
            json_response(
                429,
                {"message": "Daily limit reached.", "code": "daily_limit_exceeded", "resets_at": 1790000000},
                {"X-Daily-Limit": "500", "X-Daily-Remaining": "0"},
            )
        )

        assert isinstance(error, DailyLimitExceededError)
        assert (error.daily_limit, error.daily_remaining, error.resets_at, error.retry_after) == (500, 0, None, None)

    @pytest.mark.parametrize("value", ["Wed, 21 Oct 2026 07:28:00 GMT", "-1", "1.5", "", "١٢", str(2**53)])
    def test_ignores_rate_limit_headers_that_are_not_whole_seconds(self, value: str) -> None:
        error = error_for(
            json_response(429, {"message": "Too Many Attempts."}, {"Retry-After": value, "X-RateLimit-Limit": value})
        )

        assert isinstance(error, RateLimitedError)
        assert (error.retry_after, error.rate_limit_limit) == (None, None)

    def test_reads_rate_limit_headers_with_spaces_around_them(self) -> None:
        error = error_for(json_response(429, {"message": "Too Many Attempts."}, {"Retry-After": " 17 "}))

        assert isinstance(error, RateLimitedError)
        assert error.retry_after == 17


class TestRequestsWithoutAnAnswer:
    def test_raise_a_transport_error_that_keeps_the_cause(self) -> None:
        cause = ConnectionRefusedError("[Errno 111] Connection refused")
        error = error_for(cause)

        assert isinstance(error, TransportError)
        assert error.message == "HTTP request failed: [Errno 111] Connection refused"
        assert (error.status_code, error.trace_id) == (None, None)
        assert error.__cause__ is cause

    def test_names_a_failure_without_a_message_by_its_class(self) -> None:
        assert error_for(TimeoutError()).message == "HTTP request failed: TimeoutError"

    def test_let_an_interruption_through(self) -> None:
        class Interrupted(BaseException):
            pass

        http_client, _ = http_client_answering(Interrupted())

        with pytest.raises(Interrupted):
            http_client.get("/messages")
