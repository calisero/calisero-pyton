"""The HTTP client: authenticated JSON requests to the API, error answers turned into exceptions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, NoReturn, TypeAlias
from urllib.parse import urlencode, urlsplit

from calisero._internal.fields import to_integer
from calisero._internal.json import dumps, is_json_object, loads
from calisero.auth import AuthProvider, check_token
from calisero.errors import (
    ApiError,
    DailyLimitExceededError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    ServerError,
    TransportError,
    UnauthorizedError,
    ValidationError,
)
from calisero.http._headers import read_header_int, read_header_string
from calisero.http.request import HttpMethod, HttpRequest
from calisero.http.response import HttpResponse
from calisero.http.transport import Transport, UrllibTransport, check_timeout
from calisero.http.user_agent import AppInfo, build_user_agent

#: The production API.
DEFAULT_BASE_URL: Final = "https://rest.calisero.ro/api/v1"

#: A value of the query string; None leaves the parameter out.
QueryValue: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class HttpResult:
    """A successful answer."""

    #: The decoded JSON body; None when the answer had no body.
    body: object

    #: The raw answer, headers included.
    response: HttpResponse


class HttpClient:
    """Sends authenticated JSON requests to the API through a `Transport`.

    Error answers become the matching `ApiError`. It never retries: the API takes no
    idempotency key, so a create retried after a timeout or a server error could send
    the message twice.
    """

    def __init__(
        self,
        auth_provider: AuthProvider,
        *,
        transport: Transport | None = None,
        base_url: str = DEFAULT_BASE_URL,
        app_info: AppInfo | None = None,
    ) -> None:
        """Configure the client.

        Args:
            auth_provider: provides the API key, e.g. a `BearerTokenAuthProvider`
            transport: sends the requests: a `UrllibTransport` with its default timeout when omitted
            base_url: the API's base URL
            app_info: your application, named in the User-Agent header after the library

        Raises:
            ValueError: when the base URL is not an http(s) URL, or the application has no usable name
        """
        self._auth_provider = auth_provider
        self._transport: Transport = transport if transport is not None else UrllibTransport()
        self._base_url = _check_base_url(base_url)
        self._user_agent = build_user_agent(app_info)
        self._last_response: HttpResponse | None = None

    @property
    def base_url(self) -> str:
        """The base URL every path is appended to, without a trailing slash."""
        return self._base_url

    @property
    def user_agent(self) -> str:
        """The User-Agent header of every request.

        For example `Calisero-SMS-Python/1.0.0 (CPython 3.14.0; linux x86_64)`, then your application.
        """
        return self._user_agent

    @property
    def last_response(self) -> HttpResponse | None:
        """The raw answer to the last request, headers included.

        None before the first request and after a request that got no answer. With
        concurrent requests on the same client it is the answer that arrived last; each
        call's own answer is in its result.
        """
        return self._last_response

    def get(
        self, path: str, query: Mapping[str, QueryValue] | None = None, *, timeout: float | None = None
    ) -> HttpResult:
        return self._send("GET", self._build_url(path, query), None, timeout)

    def post(self, path: str, data: Mapping[str, object] | None = None, *, timeout: float | None = None) -> HttpResult:
        return self._send("POST", self._build_url(path), data, timeout)

    def put(self, path: str, data: Mapping[str, object] | None = None, *, timeout: float | None = None) -> HttpResult:
        return self._send("PUT", self._build_url(path), data, timeout)

    def delete(self, path: str, *, timeout: float | None = None) -> HttpResult:
        return self._send("DELETE", self._build_url(path), None, timeout)

    def _build_url(self, path: str, query: Mapping[str, QueryValue] | None = None) -> str:
        url = f"{self._base_url}/{path.lstrip('/')}"
        params = [(name, _query_value(value)) for name, value in (query or {}).items() if value is not None]

        return f"{url}?{urlencode(params)}" if params else url

    def _send(
        self, method: HttpMethod, url: str, data: Mapping[str, object] | None, timeout: float | None
    ) -> HttpResult:
        request = HttpRequest(
            method=method,
            url=url,
            headers={
                # Without it the API answers a missing or invalid key with a redirect, not a 401
                "Accept": "application/json",
                "Content-Type": "application/json",
                # Names the library, its version and the runtime, so the platform can tell its requests apart
                "User-Agent": self._user_agent,
                "Authorization": f"Bearer {check_token(self._auth_provider.get_token(), 'The API key')}",
            },
            body=dumps(dict(data)) if data else None,
            timeout=check_timeout(timeout) if timeout is not None else None,
        )

        self._last_response = None

        try:
            response = self._transport.send(request)
        except Exception as error:
            raise TransportError(f"HTTP request failed: {str(error) or type(error).__name__}") from error

        self._last_response = response

        return HttpResult(body=_handle_response(response), response=response)


def _check_base_url(base_url: str) -> str:
    """The base URL without its trailing slashes; refused unless it is an http(s) URL."""
    parts = urlsplit(base_url) if isinstance(base_url, str) else None

    if parts is None or parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"The base URL must be an http:// or https:// URL, got {base_url!r}.")

    return base_url.rstrip("/")


def _query_value(value: str | int | float | bool) -> str:
    # As the API reads booleans, not Python's True and False
    if isinstance(value, bool):
        return "true" if value else "false"

    return str(value)


def _handle_response(response: HttpResponse) -> object:
    """The decoded body of a successful answer; the error of a failed one is raised."""
    status, body = response.status, response.body

    if not 200 <= status < 300:
        _raise_error(response)

    if body.strip() == "":
        return None

    try:
        return loads(body)
    except ValueError as error:
        raise ApiError(
            f"Failed to decode JSON response: {error}", status_code=status, trace_id=_trace_id(response, {})
        ) from error


def _raise_error(response: HttpResponse) -> NoReturn:
    status = response.status
    error_details = _decode_error_body(response.body)
    message = _error_message(error_details) or f"HTTP error {status}"
    trace_id = _trace_id(response, error_details)

    if status == 401:
        raise UnauthorizedError(message, status_code=status, trace_id=trace_id, error_details=error_details)

    if status == 403:
        raise ForbiddenError(message, status_code=status, trace_id=trace_id, error_details=error_details)

    if status == 404:
        raise NotFoundError(message, status_code=status, trace_id=trace_id, error_details=error_details)

    if status == 422:
        raise ValidationError(
            message,
            status_code=status,
            trace_id=trace_id,
            error_details=error_details,
            validation_errors=_validation_errors(error_details),
        )

    if status == 429:
        raise _rate_limit_error(response, message, trace_id, error_details)

    if status in (500, 502, 503, 504):
        raise ServerError(message, status_code=status, trace_id=trace_id, error_details=error_details)

    raise ApiError(message, status_code=status, trace_id=trace_id, error_details=error_details)


def _decode_error_body(body: str) -> dict[str, object]:
    """The JSON body of an error answer; empty when it has none."""
    try:
        decoded = loads(body)
    except ValueError:
        # An error page from a proxy, or no body at all
        return {}

    return decoded if is_json_object(decoded) else {}


def _error_message(error_details: Mapping[str, object]) -> str | None:
    """The API sends the error's description as `message`; `error.message` is also read."""
    message = error_details.get("message")

    if isinstance(message, str) and message != "":
        return message

    error = error_details.get("error")

    if is_json_object(error):
        nested = error.get("message")

        if isinstance(nested, str) and nested != "":
            return nested

    return None


def _trace_id(response: HttpResponse, error_details: Mapping[str, object]) -> str | None:
    """The request's trace id.

    The X-Trace-Id header the API sends with every answer, else the trace_id of the
    error body, else an X-Request-ID header.
    """
    from_header = read_header_string(response, "X-Trace-Id")

    if from_header is not None:
        return from_header

    from_body = error_details.get("trace_id")

    if isinstance(from_body, str) and from_body != "":
        return from_body

    return read_header_string(response, "X-Request-ID")


def _validation_errors(error_details: Mapping[str, object]) -> dict[str, list[str]]:
    """The field errors of a 422 body (`errors`, or `validation_errors`); empty when it carries none."""
    errors = error_details.get("errors")

    if not is_json_object(errors):
        errors = error_details.get("validation_errors")

    if not is_json_object(errors):
        return {}

    result: dict[str, list[str]] = {}

    for field, messages in errors.items():
        if isinstance(messages, str):
            result[field] = [messages]
        elif isinstance(messages, list):
            result[field] = [message for message in messages if isinstance(message, str)]

    return result


def _rate_limit_error(
    response: HttpResponse, message: str, trace_id: str | None, error_details: dict[str, object]
) -> RateLimitedError:
    """A 429 comes from one of two limits, told apart by the body's code.

    The account's daily sending limit (daily_limit_exceeded), or the request rate limit.
    """
    retry_after = read_header_int(response, "Retry-After")
    rate_limit_limit = read_header_int(response, "X-RateLimit-Limit")
    rate_limit_remaining = read_header_int(response, "X-RateLimit-Remaining")
    rate_limit_reset = read_header_int(response, "X-RateLimit-Reset")

    if error_details.get("code") != DailyLimitExceededError.ERROR_CODE:
        return RateLimitedError(
            message,
            status_code=response.status,
            trace_id=trace_id,
            error_details=error_details,
            retry_after=retry_after,
            rate_limit_limit=rate_limit_limit,
            rate_limit_remaining=rate_limit_remaining,
            rate_limit_reset=rate_limit_reset,
        )

    daily_limit = to_integer(error_details.get("daily_limit"))
    daily_remaining = to_integer(error_details.get("daily_remaining"))
    resets_at = error_details.get("resets_at")

    return DailyLimitExceededError(
        message,
        status_code=response.status,
        trace_id=trace_id,
        error_details=error_details,
        retry_after=retry_after,
        rate_limit_limit=rate_limit_limit,
        rate_limit_remaining=rate_limit_remaining,
        rate_limit_reset=rate_limit_reset,
        daily_limit=daily_limit if daily_limit is not None else read_header_int(response, "X-Daily-Limit"),
        daily_remaining=(
            daily_remaining if daily_remaining is not None else read_header_int(response, "X-Daily-Remaining")
        ),
        resets_at=resets_at if isinstance(resets_at, str) else None,
    )
