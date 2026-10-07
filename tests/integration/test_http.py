"""The library over real HTTP: the default urllib transport against a local server."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from calisero import (
    VERSION,
    ApiError,
    DailyLimitExceededError,
    ServerError,
    SmsClient,
    TransportError,
    ValidationError,
)
from calisero.http.user_agent import RUNTIME
from tests.support.fixtures import DAILY_LIMIT_BODY, MESSAGE_ID, PHONE, TRACE_ID, message_data, page_of
from tests.support.local_server import Answer, ReceivedRequest, free_port, json_answer, local_server


def client_for(url: str, timeout: float = 5) -> SmsClient:
    return SmsClient.create("integration-key", base_url=f"{url}/api/v1", timeout=timeout)


def test_sends_an_authenticated_json_request_and_reads_the_answer_and_its_headers() -> None:
    body = "Bună ziua! Ștefan, țară, încă"
    headers = {
        "X-Trace-Id": TRACE_ID,
        "X-RateLimit-Limit": "240",
        "X-RateLimit-Remaining": "239",
        "X-Daily-Limit": "1000",
        "X-Daily-Remaining": "999",
    }

    with local_server(lambda _: json_answer(201, {"data": message_data(body=body)}, headers)) as server:
        response = client_for(server.url).messages.create(recipient=PHONE, body=body, shorten_urls=False)

    [received] = server.received
    assert (received.method, received.target) == ("POST", "/api/v1/messages")
    assert received.headers["accept"] == "application/json"
    assert received.headers["content-type"] == "application/json"
    assert received.headers["authorization"] == "Bearer integration-key"
    runtime = f"({RUNTIME.implementation} {RUNTIME.version}; {RUNTIME.system} {RUNTIME.machine})"
    assert received.headers["user-agent"] == f"Calisero-SMS-Python/{VERSION} {runtime}"
    assert json.loads(received.text) == {"recipient": PHONE, "body": body, "shorten_urls": False}
    assert response.data.body == body
    assert (
        response.response_meta.trace_id,
        response.response_meta.rate_limit_limit,
        response.response_meta.rate_limit_remaining,
        response.response_meta.daily_limit,
        response.response_meta.daily_remaining,
    ) == (TRACE_ID, 240, 239, 1000, 999)


def test_sends_the_query_of_a_list_and_reads_the_page() -> None:
    with local_server(lambda _: json_answer(200, page_of([message_data()], "messages", 2, True))) as server:
        page = client_for(server.url).messages.list(page=2)

    assert server.received[0].target == "/api/v1/messages?page=2"
    assert page.data[0].id == MESSAGE_ID
    assert page.has_next_page


def test_cancels_a_message_answered_with_an_empty_list() -> None:
    with local_server(lambda _: json_answer(200, [])) as server:
        client_for(server.url).messages.delete(MESSAGE_ID)

    received = server.received[0]
    assert (received.method, received.target, received.body) == ("DELETE", f"/api/v1/messages/{MESSAGE_ID}", b"")


def test_turns_a_daily_limit_refusal_into_a_daily_limit_exceeded_error() -> None:
    headers = {"Retry-After": "21600", "X-Daily-Limit": "1000", "X-Daily-Remaining": "0", "X-Trace-Id": TRACE_ID}

    with (
        local_server(lambda _: json_answer(429, DAILY_LIMIT_BODY, headers)) as server,
        pytest.raises(DailyLimitExceededError) as caught,
    ):
        client_for(server.url).messages.create(recipient=PHONE, body="Hello")

    error = caught.value
    assert (error.status_code, error.trace_id, error.retry_after) == (429, TRACE_ID, 21600)
    assert (error.daily_limit, error.daily_remaining, error.resets_at) == (1000, 0, "2026-10-01T00:00:00+03:00")


def test_turns_validation_errors_into_a_validation_error() -> None:
    body = {
        "message": "The recipient field is required.",
        "errors": {"recipient": ["The recipient field is required."]},
        "trace_id": TRACE_ID,
    }

    with local_server(lambda _: json_answer(422, body)) as server, pytest.raises(ValidationError) as caught:
        client_for(server.url).messages.create(recipient="", body="Hello")

    assert caught.value.trace_id == TRACE_ID
    assert caught.value.validation_errors == {"recipient": ["The recipient field is required."]}


def test_turns_an_html_error_page_into_a_server_error() -> None:
    page = Answer(502, "<html><body>Bad Gateway</body></html>", {"Content-Type": "text/html"})

    with local_server(lambda _: page) as server, pytest.raises(ServerError, match=r"^HTTP error 502$"):
        client_for(server.url).accounts.get("acc")


def test_does_not_follow_a_redirect_so_the_key_never_leaves() -> None:
    def handle(request: ReceivedRequest) -> Answer:
        return Answer(302, b"", {"Location": "/login"})

    with local_server(handle) as server, pytest.raises(ApiError) as caught:
        client_for(server.url).messages.list()

    assert type(caught.value) is ApiError
    assert caught.value.status_code == 302
    assert [received.target for received in server.received] == ["/api/v1/messages"]


def test_gives_up_after_the_timeout() -> None:
    with (
        local_server(lambda _: Answer(200, b"{}", delay=5)) as server,
        pytest.raises(TransportError, match=r"^HTTP request failed: Request timed out after 0\.2 s$") as caught,
    ):
        client_for(server.url, timeout=0.2).messages.list()

    assert isinstance(caught.value.__cause__, TimeoutError)
    assert caught.value.status_code is None


def test_gives_up_after_the_timeout_of_a_call() -> None:
    with (
        local_server(lambda _: Answer(200, b"{}", delay=5)) as server,
        pytest.raises(TransportError, match=r"timed out after 0\.2 s$"),
    ):
        client_for(server.url, timeout=30).messages.list(timeout=0.2)


def test_raises_a_transport_error_when_the_connection_is_refused() -> None:
    client = client_for(f"http://127.0.0.1:{free_port()}")

    with pytest.raises(TransportError, match=r"^HTTP request failed: .*[Rr]efused") as caught:
        client.messages.list()

    assert isinstance(caught.value.__cause__, ConnectionError)
    assert client.http_client.last_response is None


def test_answers_concurrent_requests_each_with_its_own_answer() -> None:
    def handle(request: ReceivedRequest) -> Answer:
        message_id = request.target.rsplit("/", 1)[-1]

        return json_answer(200, {"data": message_data(id=message_id)}, {"X-Trace-Id": f"trace-{message_id}"})

    with local_server(handle) as server:
        client = client_for(server.url)

        with ThreadPoolExecutor(max_workers=20) as pool:
            responses = list(pool.map(lambda index: client.messages.get(f"msg-{index}"), range(20)))

    assert [response.data.id for response in responses] == [f"msg-{index}" for index in range(20)]
    assert [response.response_meta.trace_id for response in responses] == [f"trace-msg-{index}" for index in range(20)]


def test_sends_through_a_proxy() -> None:
    with local_server(lambda _: json_answer(200, page_of([], "messages"))) as proxy:
        client = SmsClient.create("integration-key", base_url="http://calisero.invalid/api/v1", proxy=proxy.url)

        client.messages.list(page=2)

    received = proxy.received[0]
    assert received.target == "http://calisero.invalid/api/v1/messages?page=2"
    assert received.headers["authorization"] == "Bearer integration-key"
