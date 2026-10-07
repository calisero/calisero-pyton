"""A handler for the delivery status callbacks: for any web framework, and as a WSGI application."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import parse_qs

from calisero._internal.json import dumps
from calisero.errors import InvalidWebhookPayloadError
from calisero.webhooks.message import DeliveryWebhookMessage

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment


@dataclass(frozen=True, slots=True)
class WebhookResponse:
    """The answer to give Calisero: a status, a JSON body and, for a 405, an Allow header."""

    status: int
    body: dict[str, object]
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def content(self) -> bytes:
        """The body as JSON, encoded in UTF-8."""
        return dumps(self.body).encode("utf-8")


class _PayloadTooLargeError(InvalidWebhookPayloadError):
    """The body is larger than the handler accepts."""


class DeliveryWebhookHandler:
    """Answers the delivery status callbacks Calisero posts to the messages' callback URLs.

    Call `handle()` from a view of any web framework, or mount the handler itself: it is
    a WSGI application. The answers:

    - 200 `{"received": true}` once `on_message` handled the update;
    - 400 for a payload that is not a delivery status update, 413 for one too large;
    - 401 when `token` is set and the request lacks it;
    - 405 for anything but POST;
    - 500 when `on_message` raises. Calisero retries only a callback that got no answer
      within 2 seconds, never one answered with an error.
    """

    #: The largest body accepted by default, in bytes: 64 KiB.
    DEFAULT_MAX_BODY_SIZE: ClassVar[int] = 64 * 1024

    def __init__(
        self,
        on_message: Callable[[DeliveryWebhookMessage], object],
        *,
        token: str | None = None,
        on_error: Callable[[Exception], object] | None = None,
        max_body_size: int = DEFAULT_MAX_BODY_SIZE,
    ) -> None:
        """Configure the handler.

        Args:
            on_message: called with every delivery status update. The answer is given once it
                returns, and Calisero waits 2 seconds for it: record the status or queue a job,
                then return.
            token: a secret the callback URL carries as its `token` query parameter, e.g.
                https://yourapp.com/webhooks/calisero?token=...: a request without it is answered
                401. Calisero does not sign its callbacks, so this is how to accept only the
                callbacks of the URLs you gave it.
            on_error: called when a request is refused or `on_message` fails, e.g. to log it
            max_body_size: the largest body accepted, in bytes

        Raises:
            TypeError: when on_message is not callable, or an argument is not of its type
            ValueError: when the token is empty or the largest body size is not positive
        """
        if not callable(on_message):
            raise TypeError("DeliveryWebhookHandler needs an on_message function.")

        if token is not None and not isinstance(token, str):
            raise TypeError("The webhook token must be a non-empty string.")

        if token == "":
            raise ValueError("The webhook token must be a non-empty string.")

        size_message = f"max_body_size must be a positive number of bytes, got {max_body_size!r}."

        if isinstance(max_body_size, bool) or not isinstance(max_body_size, int):
            raise TypeError(size_message)

        if max_body_size <= 0:
            raise ValueError(size_message)

        self._on_message = on_message
        self._on_error = on_error
        self._token = token
        self._max_body_size = max_body_size

    @property
    def max_body_size(self) -> int:
        """The largest body accepted, in bytes."""
        return self._max_body_size

    def handle(self, body: object, *, method: str = "POST", token: str | None = None) -> WebhookResponse:
        """Handle a callback request and tell how to answer it.

        Args:
            body: the request's raw body (bytes or str), or the JSON your framework decoded
            method: the request's HTTP method
            token: the `token` query parameter of the request, if any
        """
        refusal = self._refusal(method, token)

        if refusal is not None:
            return refusal

        if _size(body) > self._max_body_size:
            return self._too_large()

        try:
            message = _read_message(body)
        except InvalidWebhookPayloadError as error:
            self._report(error)

            return WebhookResponse(400, {"error": "Invalid payload"})

        try:
            self._on_message(message)
        except Exception as error:
            self._report(error)

            return WebhookResponse(500, {"error": "Webhook handler failed"})

        return WebhookResponse(200, {"received": True})

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        """Answer a callback as a WSGI application, at whatever path it is mounted."""
        method = str(environ.get("REQUEST_METHOD", "GET"))
        token = _query_token(str(environ.get("QUERY_STRING", "")))

        # Refused before its body is read
        response = self._refusal(method, token)

        if response is None:
            body = _read_wsgi_body(environ, self._max_body_size)
            response = self._too_large() if body is None else self.handle(body, method=method, token=token)

        content = response.content
        start_response(
            f"{response.status} {HTTPStatus(response.status).phrase}",
            [("Content-Type", "application/json"), ("Content-Length", str(len(content))), *response.headers.items()],
        )

        return [content]

    def _refusal(self, method: str, token: str | None) -> WebhookResponse | None:
        """The answer to a request refused whatever its body: not a POST, or without the token."""
        if method.upper() != "POST":
            return WebhookResponse(405, {"error": "Method not allowed"}, {"Allow": "POST"})

        if self._token is not None and not _token_matches(token, self._token):
            self._report(PermissionError("Invalid webhook token: the request URL lacks the expected token."))

            return WebhookResponse(401, {"error": "Invalid webhook token"})

        return None

    def _too_large(self) -> WebhookResponse:
        self._report(
            _PayloadTooLargeError(f"Invalid delivery webhook payload: larger than {self._max_body_size} bytes.")
        )

        return WebhookResponse(413, {"error": "Payload too large"})

    def _report(self, error: Exception) -> None:
        if self._on_error is not None:
            self._on_error(error)


def _read_message(body: object) -> DeliveryWebhookMessage:
    if isinstance(body, (str, bytes, bytearray, memoryview)):
        return DeliveryWebhookMessage.from_json(body)

    if body is None:
        return DeliveryWebhookMessage.from_json("")

    # The JSON a web framework decoded
    return DeliveryWebhookMessage.from_dict(body)


def _size(body: object) -> int:
    """The size of a raw body, in bytes; 0 for a body a framework already decoded."""
    if isinstance(body, str):
        return len(body.encode("utf-8"))

    if isinstance(body, (bytes, bytearray)):
        return len(body)

    if isinstance(body, memoryview):
        return body.nbytes

    return 0


def _token_matches(provided: str | None, expected: str) -> bool:
    if provided is None:
        return False

    # Digests of equal length, compared in constant time
    return hmac.compare_digest(_sha256(provided), _sha256(expected))


def _sha256(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def _query_token(query_string: str) -> str | None:
    values = parse_qs(query_string, keep_blank_values=True).get("token")

    return values[0] if values else None


def _read_wsgi_body(environ: WSGIEnvironment, max_body_size: int) -> bytes | None:
    """The body of a WSGI request; None when it is larger than `max_body_size`."""
    stream = environ.get("wsgi.input")

    if stream is None:
        return b""

    length = str(environ.get("CONTENT_LENGTH") or "").strip()

    if length != "":
        try:
            size = int(length)
        except ValueError:
            return b""

        if size > max_body_size:
            return None

        return bytes(stream.read(size)) if size > 0 else b""

    # Without a length (a chunked body), read only from a server that marks where the body ends:
    # reading past it would wait for a client that sends nothing more
    if environ.get("wsgi.input_terminated"):
        data = bytes(stream.read(max_body_size + 1))

        return None if len(data) > max_body_size else data

    return b""
