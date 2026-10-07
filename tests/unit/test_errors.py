from __future__ import annotations

import pickle

import pytest

from calisero import (
    ApiError,
    CaliseroError,
    DailyLimitExceededError,
    ForbiddenError,
    InvalidWebhookPayloadError,
    NotFoundError,
    RateLimitedError,
    ServerError,
    TransportError,
    UnauthorizedError,
    ValidationError,
)
from tests.support.fixtures import TRACE_ID


@pytest.mark.parametrize(
    "error_class",
    [
        UnauthorizedError,
        ForbiddenError,
        NotFoundError,
        ValidationError,
        RateLimitedError,
        DailyLimitExceededError,
        ServerError,
        TransportError,
    ],
)
def test_every_api_error_is_an_api_error_and_a_calisero_error(error_class: type[ApiError]) -> None:
    error = error_class("Refused")

    assert isinstance(error, ApiError)
    assert isinstance(error, CaliseroError)
    assert isinstance(error, Exception)


def test_the_daily_limit_refusal_is_a_rate_limit_refusal() -> None:
    assert issubclass(DailyLimitExceededError, RateLimitedError)
    assert not issubclass(RateLimitedError, DailyLimitExceededError)


def test_an_invalid_webhook_payload_is_a_value_error_not_an_api_error() -> None:
    error = InvalidWebhookPayloadError("Invalid delivery webhook payload")

    assert isinstance(error, CaliseroError)
    assert isinstance(error, ValueError)
    assert not isinstance(error, ApiError)


def test_an_api_error_has_defaults() -> None:
    error = ApiError()

    assert error.message == ""
    assert str(error) == ""
    assert error.status_code is None
    assert error.trace_id is None
    assert error.request_id is None
    assert error.error_details == {}


def test_an_api_error_carries_the_answer() -> None:
    details = {"message": "Resource not found!", "trace_id": TRACE_ID}
    error = NotFoundError("Resource not found!", status_code=404, trace_id=TRACE_ID, error_details=details)

    assert str(error) == "Resource not found!"
    assert error.message == "Resource not found!"
    assert error.status_code == 404
    assert error.trace_id == TRACE_ID
    assert error.request_id == TRACE_ID
    assert error.error_details == details


def test_an_api_error_keeps_a_copy_of_the_details() -> None:
    details: dict[str, object] = {"message": "Refused"}
    error = ApiError("Refused", error_details=details)

    details["message"] = "Changed"

    assert error.error_details == {"message": "Refused"}


def test_a_validation_error_carries_the_field_errors() -> None:
    assert ValidationError("Invalid.").validation_errors == {}

    error = ValidationError("Invalid.", validation_errors={"recipient": ("The recipient field is required.",)})

    assert error.validation_errors == {"recipient": ["The recipient field is required."]}


def test_a_rate_limit_error_carries_the_limits() -> None:
    error = RateLimitedError(
        "Too Many Attempts.",
        status_code=429,
        retry_after=17,
        rate_limit_limit=240,
        rate_limit_remaining=0,
        rate_limit_reset=1790000000,
    )

    assert (error.retry_after, error.rate_limit_limit, error.rate_limit_remaining, error.rate_limit_reset) == (
        17,
        240,
        0,
        1790000000,
    )
    assert RateLimitedError().retry_after is None


def test_a_daily_limit_error_carries_the_daily_limit() -> None:
    error = DailyLimitExceededError(
        "Daily limit reached.",
        status_code=429,
        retry_after=21600,
        daily_limit=1000,
        daily_remaining=0,
        resets_at="2026-10-01T00:00:00+03:00",
    )

    assert DailyLimitExceededError.ERROR_CODE == "daily_limit_exceeded"
    assert (error.daily_limit, error.daily_remaining, error.resets_at) == (1000, 0, "2026-10-01T00:00:00+03:00")
    assert error.retry_after == 21600
    assert DailyLimitExceededError().resets_at is None


def test_errors_survive_pickling_with_their_attributes() -> None:
    error = DailyLimitExceededError("Daily limit reached.", status_code=429, trace_id=TRACE_ID, daily_limit=1000)

    copy = pickle.loads(pickle.dumps(error))  # noqa: S301 - our own object

    assert type(copy) is DailyLimitExceededError
    assert (copy.message, copy.status_code, copy.trace_id, copy.daily_limit) == (
        "Daily limit reached.",
        429,
        TRACE_ID,
        1000,
    )
