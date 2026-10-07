from __future__ import annotations

import io
import json
from collections.abc import Callable, Iterable
from typing import Any
from wsgiref.util import setup_testing_defaults

import pytest

from calisero import DeliveryWebhookHandler, DeliveryWebhookMessage, InvalidWebhookPayloadError, WebhookResponse
from tests.support.fixtures import webhook_payload, without
from tests.support.local_server import send, wsgi_server

PAYLOAD = json.dumps(webhook_payload()).encode()


class Recorder:
    """Records the messages and the errors the handler reports."""

    def __init__(self) -> None:
        self.messages: list[DeliveryWebhookMessage] = []
        self.errors: list[Exception] = []

    def on_message(self, message: DeliveryWebhookMessage) -> None:
        self.messages.append(message)

    def on_error(self, error: Exception) -> None:
        self.errors.append(error)


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


def handler_for(recorder: Recorder, **options: Any) -> DeliveryWebhookHandler:
    return DeliveryWebhookHandler(recorder.on_message, on_error=recorder.on_error, **options)


class TestHandle:
    @pytest.mark.parametrize("body", [PAYLOAD, PAYLOAD.decode(), bytearray(PAYLOAD), webhook_payload()])
    def test_hands_the_update_to_on_message_and_answers_200(self, recorder: Recorder, body: object) -> None:
        response = handler_for(recorder).handle(body)

        assert response == WebhookResponse(200, {"received": True})
        assert response.content == b'{"received":true}'
        assert [message.status for message in recorder.messages] == ["delivered"]
        assert recorder.errors == []

    def test_answers_405_to_anything_but_post(self, recorder: Recorder) -> None:
        response = handler_for(recorder).handle(PAYLOAD, method="GET")

        assert response == WebhookResponse(405, {"error": "Method not allowed"}, {"Allow": "POST"})
        assert (recorder.messages, recorder.errors) == ([], [])

    def test_reads_the_method_in_any_case(self, recorder: Recorder) -> None:
        assert handler_for(recorder).handle(PAYLOAD, method="post").status == 200

    @pytest.mark.parametrize(
        "body",
        [b"{not json", b"[]", b"", None, json.dumps(without(webhook_payload(), "messageId")).encode(), [1, 2]],
    )
    def test_answers_400_to_a_payload_that_is_not_an_update_and_reports_it(
        self, recorder: Recorder, body: object
    ) -> None:
        response = handler_for(recorder).handle(body)

        assert response == WebhookResponse(400, {"error": "Invalid payload"})
        assert recorder.messages == []
        assert len(recorder.errors) == 1
        assert isinstance(recorder.errors[0], InvalidWebhookPayloadError)

    def test_answers_413_to_a_payload_larger_than_the_limit(self, recorder: Recorder) -> None:
        body = json.dumps(webhook_payload(sender="x" * 200))

        response = handler_for(recorder, max_body_size=100).handle(body)

        assert response == WebhookResponse(413, {"error": "Payload too large"})
        assert str(recorder.errors[0]) == "Invalid delivery webhook payload: larger than 100 bytes."
        assert isinstance(recorder.errors[0], InvalidWebhookPayloadError)

    def test_measures_a_text_body_in_bytes(self, recorder: Recorder) -> None:
        text = json.dumps(webhook_payload(sender="ș" * 40), ensure_ascii=False)
        limit = len(text) + 10

        assert handler_for(recorder, max_body_size=limit).handle(text).status == 413
        assert handler_for(recorder, max_body_size=limit).handle(memoryview(PAYLOAD)).status == 200

    def test_does_not_measure_a_payload_the_framework_decoded(self, recorder: Recorder) -> None:
        assert handler_for(recorder, max_body_size=10).handle(webhook_payload()).status == 200

    def test_answers_500_when_on_message_fails_and_reports_it(self, recorder: Recorder) -> None:
        failure = RuntimeError("Database down")

        def on_message(message: DeliveryWebhookMessage) -> None:
            raise failure

        handler = DeliveryWebhookHandler(on_message, on_error=recorder.on_error)

        assert handler.handle(PAYLOAD) == WebhookResponse(500, {"error": "Webhook handler failed"})
        assert recorder.errors == [failure]

    def test_lets_an_interruption_of_on_message_through(self) -> None:
        class Interrupted(BaseException):
            pass

        def on_message(message: DeliveryWebhookMessage) -> None:
            raise Interrupted

        with pytest.raises(Interrupted):
            DeliveryWebhookHandler(on_message).handle(PAYLOAD)

    def test_answers_without_an_error_callback(self) -> None:
        handler = DeliveryWebhookHandler(lambda message: None)

        assert handler.handle(b"{not json").status == 400
        assert handler.max_body_size == DeliveryWebhookHandler.DEFAULT_MAX_BODY_SIZE == 64 * 1024


class TestToken:
    def test_accepts_a_request_that_carries_the_token(self, recorder: Recorder) -> None:
        response = handler_for(recorder, token="s3cr3t-t0ken").handle(PAYLOAD, token="s3cr3t-t0ken")

        assert response.status == 200
        assert len(recorder.messages) == 1

    @pytest.mark.parametrize("token", [None, "guess", "s3cr3t-t0ken-and-more", ""])
    def test_answers_401_to_a_request_without_the_token(self, recorder: Recorder, token: str | None) -> None:
        response = handler_for(recorder, token="s3cr3t-t0ken").handle(PAYLOAD, token=token)

        assert response == WebhookResponse(401, {"error": "Invalid webhook token"})
        assert recorder.messages == []
        assert isinstance(recorder.errors[0], PermissionError)
        assert str(recorder.errors[0]) == "Invalid webhook token: the request URL lacks the expected token."

    def test_refuses_the_token_before_reading_the_body(self, recorder: Recorder) -> None:
        response = handler_for(recorder, token="s3cr3t-t0ken", max_body_size=10).handle(PAYLOAD, token="guess")

        assert response.status == 401


class TestOptions:
    def test_refuses_an_on_message_that_cannot_be_called(self) -> None:
        with pytest.raises(TypeError, match=r"^DeliveryWebhookHandler needs an on_message function\.$"):
            DeliveryWebhookHandler(None)  # type: ignore[arg-type]

    @pytest.mark.parametrize(("token", "error"), [("", ValueError), (42, TypeError)])
    def test_refuses_an_empty_token(self, token: object, error: type[Exception]) -> None:
        with pytest.raises(error, match=r"^The webhook token must be a non-empty string\.$"):
            DeliveryWebhookHandler(lambda message: None, token=token)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("size", "error"), [(0, ValueError), (-1, ValueError), (True, TypeError), ("1", TypeError)]
    )
    def test_refuses_a_body_size_that_is_not_positive(self, size: object, error: type[Exception]) -> None:
        with pytest.raises(error, match=r"^max_body_size must be a positive number of bytes, got "):
            DeliveryWebhookHandler(lambda message: None, max_body_size=size)  # type: ignore[arg-type]


class StartResponse:
    """The start_response of a WSGI server, recording the status and the headers."""

    def __init__(self) -> None:
        self.status = ""
        self.headers: list[tuple[str, str]] = []

    def __call__(
        self, status: str, headers: list[tuple[str, str]], exc_info: object = None, /
    ) -> Callable[[bytes], object]:
        self.status = status
        self.headers = headers

        return lambda data: None


class UnreadableInput(io.BytesIO):
    def read(self, size: int | None = -1) -> bytes:
        raise AssertionError("The body was read")


def call_wsgi(
    handler: DeliveryWebhookHandler,
    method: str = "POST",
    query: str = "",
    environ: dict[str, Any] | None = None,
) -> tuple[StartResponse, dict[str, Any]]:
    """Call the handler as a WSGI server does, with PAYLOAD as the body unless `environ` says otherwise."""
    env: dict[str, Any] = {
        "REQUEST_METHOD": method,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(PAYLOAD)),
        "wsgi.input": io.BytesIO(PAYLOAD),
        **(environ or {}),
    }
    setup_testing_defaults(env)
    start_response = StartResponse()
    content: Iterable[bytes] = handler(env, start_response)

    return start_response, json.loads(b"".join(content))


class TestWsgiApplication:
    def test_answers_a_callback(self, recorder: Recorder) -> None:
        start_response, body = call_wsgi(handler_for(recorder))

        assert start_response.status == "200 OK"
        assert start_response.headers == [("Content-Type", "application/json"), ("Content-Length", "17")]
        assert body == {"received": True}
        assert recorder.messages[0].message_id == "019961db-14a7-7348-963f-5a7a789a969f"

    def test_reads_the_token_from_the_query_string(self, recorder: Recorder) -> None:
        handler = handler_for(recorder, token="s3cr3t")

        assert call_wsgi(handler, query="token=s3cr3t&other=1")[0].status == "200 OK"
        assert call_wsgi(handler, query="token=")[0].status == "401 Unauthorized"
        assert call_wsgi(handler, query="other=s3cr3t")[0].status == "401 Unauthorized"

    def test_refuses_a_request_before_reading_its_body(self, recorder: Recorder) -> None:
        handler = handler_for(recorder, token="s3cr3t")

        start_response, body = call_wsgi(handler, method="GET", environ={"wsgi.input": UnreadableInput()})
        assert start_response.status == "405 Method Not Allowed"
        assert ("Allow", "POST") in start_response.headers
        assert body == {"error": "Method not allowed"}

        assert call_wsgi(handler, environ={"wsgi.input": UnreadableInput()})[0].status == "401 Unauthorized"

    def test_answers_413_to_a_declared_length_over_the_limit_without_reading_the_body(self, recorder: Recorder) -> None:
        environ = {"CONTENT_LENGTH": "5000", "wsgi.input": UnreadableInput()}

        start_response, body = call_wsgi(handler_for(recorder, max_body_size=100), environ=environ)

        # The reason phrase is "Content Too Large" from Python 3.13 on, as RFC 9110 names it
        assert start_response.status.startswith("413 ")
        assert body == {"error": "Payload too large"}
        assert isinstance(recorder.errors[0], InvalidWebhookPayloadError)

    def test_reads_a_body_without_a_length_from_a_server_that_marks_its_end(self, recorder: Recorder) -> None:
        environ = {"CONTENT_LENGTH": "", "wsgi.input_terminated": True}

        assert call_wsgi(handler_for(recorder), environ=environ)[0].status == "200 OK"

    def test_refuses_a_body_without_a_length_over_the_limit(self, recorder: Recorder) -> None:
        environ = {"CONTENT_LENGTH": "", "wsgi.input_terminated": True}

        start_response, _ = call_wsgi(handler_for(recorder, max_body_size=100), environ=environ)

        assert start_response.status.startswith("413 ")

    def test_does_not_wait_for_a_body_without_a_length_otherwise(self, recorder: Recorder) -> None:
        environ = {"CONTENT_LENGTH": "", "wsgi.input": UnreadableInput()}

        assert call_wsgi(handler_for(recorder), environ=environ)[0].status == "400 Bad Request"

    @pytest.mark.parametrize("length", ["0", "-5", "abc"])
    def test_answers_400_to_a_length_without_a_body(self, recorder: Recorder, length: str) -> None:
        assert call_wsgi(handler_for(recorder), environ={"CONTENT_LENGTH": length})[0].status == "400 Bad Request"

    def test_answers_400_without_an_input_stream(self, recorder: Recorder) -> None:
        handler = handler_for(recorder)
        environ: dict[str, Any] = {"REQUEST_METHOD": "POST", "CONTENT_LENGTH": "10"}
        start_response = StartResponse()

        content = b"".join(handler(environ, start_response))

        assert start_response.status == "400 Bad Request"
        assert json.loads(content) == {"error": "Invalid payload"}

    def test_answers_over_real_http(self, recorder: Recorder) -> None:
        with wsgi_server(handler_for(recorder, token="s3cr3t")) as server:
            accepted = send("POST", f"{server.url}/webhooks/calisero?token=s3cr3t", PAYLOAD)
            refused = send("POST", f"{server.url}/webhooks/calisero", PAYLOAD)
            invalid = send("POST", f"{server.url}/webhooks/calisero?token=s3cr3t", b"[]")

        assert (accepted.status, accepted.headers["content-type"], accepted.json()) == (
            200,
            "application/json",
            {"received": True},
        )
        assert (refused.status, refused.json()) == (401, {"error": "Invalid webhook token"})
        assert invalid.status == 400
        assert [message.recipient for message in recorder.messages] == ["+40742***350"]
