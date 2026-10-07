"""The exceptions the library raises."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import ClassVar


class CaliseroError(Exception):
    """Base class of the exceptions the library raises: API errors and invalid webhook payloads.

    Arguments that cannot be sent at all (an empty id, a page that is not a positive
    integer, a naive datetime) raise the built-in TypeError or ValueError instead,
    before any request is made.
    """


class ApiError(CaliseroError):
    """Base exception for all Calisero API related errors."""

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int | None = None,
        trace_id: str | None = None,
        error_details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)

        #: The API's description of the error.
        self.message: str = message

        #: The HTTP status of the answer; None when the request got no answer.
        self.status_code: int | None = status_code

        #: The request's trace id, from the X-Trace-Id header or the error body's trace_id: quote it to
        #: Calisero support, or look the request up in the dashboard under Developers → Debug.
        self.trace_id: str | None = trace_id

        #: The decoded error body; empty when the answer had none.
        self.error_details: dict[str, object] = dict(error_details) if error_details is not None else {}

    @property
    def request_id(self) -> str | None:
        """The request's trace id, the same as `trace_id`."""
        return self.trace_id


class UnauthorizedError(ApiError):
    """Raised when authentication fails (401): the API key is missing, invalid or revoked."""


class ForbiddenError(ApiError):
    """Raised when access is forbidden (403), e.g. deleting a message already sent."""


class NotFoundError(ApiError):
    """Raised when a resource is not found (404)."""


class ValidationError(ApiError):
    """Raised for validation errors (422): the request's data was refused."""

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int | None = None,
        trace_id: str | None = None,
        error_details: Mapping[str, object] | None = None,
        validation_errors: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, trace_id=trace_id, error_details=error_details)

        #: The field errors, e.g. {"recipient": ["The recipient field is required."]}; empty when the
        #: answer carried none.
        self.validation_errors: dict[str, list[str]] = {
            field: list(messages) for field, messages in (validation_errors or {}).items()
        }


class RateLimitedError(ApiError):
    """Raised when the request rate limit is exceeded (429).

    This is the request rate limit (each API user may make 240 requests a minute); a
    refusal of the account's daily sending limit is raised as the subclass
    `DailyLimitExceededError`.
    """

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int | None = None,
        trace_id: str | None = None,
        error_details: Mapping[str, object] | None = None,
        retry_after: int | None = None,
        rate_limit_limit: int | None = None,
        rate_limit_remaining: int | None = None,
        rate_limit_reset: int | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, trace_id=trace_id, error_details=error_details)

        #: Seconds to wait before sending again (the Retry-After header).
        self.retry_after: int | None = retry_after

        #: How many requests the API user may make a minute (the X-RateLimit-Limit header).
        self.rate_limit_limit: int | None = rate_limit_limit

        #: How many requests the API user may still make this minute (the X-RateLimit-Remaining
        #: header): 0 when the request rate limit refused the request.
        self.rate_limit_remaining: int | None = rate_limit_remaining

        #: When requests are accepted again, as a Unix timestamp (the X-RateLimit-Reset header);
        #: sent only when the request rate limit refused the request.
        self.rate_limit_reset: int | None = rate_limit_reset


class DailyLimitExceededError(RateLimitedError):
    """Raised when the account reached its daily sending limit (429 with the code `daily_limit_exceeded`).

    Nothing was sent and nothing was billed. The limit resets at midnight, Romania time
    (`resets_at`); test messages never count towards it. It extends `RateLimitedError`,
    so code that catches that one keeps catching this refusal too.
    """

    #: The `code` of the error body that tells this refusal from the request rate limit's.
    ERROR_CODE: ClassVar[str] = "daily_limit_exceeded"

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int | None = None,
        trace_id: str | None = None,
        error_details: Mapping[str, object] | None = None,
        retry_after: int | None = None,
        rate_limit_limit: int | None = None,
        rate_limit_remaining: int | None = None,
        rate_limit_reset: int | None = None,
        daily_limit: int | None = None,
        daily_remaining: int | None = None,
        resets_at: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            trace_id=trace_id,
            error_details=error_details,
            retry_after=retry_after,
            rate_limit_limit=rate_limit_limit,
            rate_limit_remaining=rate_limit_remaining,
            rate_limit_reset=rate_limit_reset,
        )

        #: How many messages the account can send in a day.
        self.daily_limit: int | None = daily_limit

        #: How many messages the account can still send today: 0 once the limit is reached.
        self.daily_remaining: int | None = daily_remaining

        #: The next midnight, Romania time, when the account can send again, as an ISO 8601
        #: date-time (e.g. 2026-10-01T00:00:00+03:00).
        self.resets_at: str | None = resets_at


class ServerError(ApiError):
    """Raised for server errors (500, 502, 503, 504)."""


class TransportError(ApiError):
    """Raised when the request got no answer: network error or timeout.

    The original exception is its `__cause__`.
    """


class InvalidWebhookPayloadError(CaliseroError, ValueError):
    """Raised when a delivery status callback is not the payload Calisero sends.

    Not JSON, not an object, or a required field missing or malformed.
    """
