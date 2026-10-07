from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from calisero.http._headers import read_header_int, read_header_string
from calisero.http.response import HttpResponse

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ResponseMeta:
    """What the API reports in the headers of an answer.

    The request's trace id, the request rate limit and, for a created message or
    verification, the account's daily sending limit. A value is None when the answer
    did not carry it.
    """

    #: The request's trace id (X-Trace-Id): quote it to Calisero support, or look the request up in
    #: the dashboard under Developers → Debug.
    trace_id: str | None = None

    #: How many requests the API user may make a minute (X-RateLimit-Limit).
    rate_limit_limit: int | None = None

    #: How many requests the API user may still make this minute (X-RateLimit-Remaining).
    rate_limit_remaining: int | None = None

    #: How many messages the account can send in a day (X-Daily-Limit); None when no daily limit
    #: applies or the answer is not to a created message or verification.
    daily_limit: int | None = None

    #: How many messages the account can still send today, after this one (X-Daily-Remaining);
    #: None when no daily limit applies.
    daily_remaining: int | None = None

    @classmethod
    def from_response(cls, response: HttpResponse | None) -> ResponseMeta:
        """Read the headers of an answer; every value is None when there is no answer."""
        if response is None:
            return cls()

        return cls(
            trace_id=read_header_string(response, "X-Trace-Id"),
            rate_limit_limit=read_header_int(response, "X-RateLimit-Limit"),
            rate_limit_remaining=read_header_int(response, "X-RateLimit-Remaining"),
            daily_limit=read_header_int(response, "X-Daily-Limit"),
            daily_remaining=read_header_int(response, "X-Daily-Remaining"),
        )


@dataclass(frozen=True)
class ApiResponse(Generic[T]):
    """A single resource as the API answers it: the resource (`data`) and what the answer's headers report."""

    data: T

    #: The answer's headers: trace id, request rate limit and, for a created message or
    #: verification, what is left of the account's daily sending limit.
    response_meta: ResponseMeta = field(default_factory=ResponseMeta)
