from __future__ import annotations

import ssl
import urllib.error

import pytest

from calisero import HttpRequest, UrllibTransport
from tests.support.local_server import Answer, free_port, json_answer, local_server


def request(url: str, method: str = "GET", body: str | None = None, timeout: float | None = None) -> HttpRequest:
    headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer key"}

    return HttpRequest(method=method, url=url, headers=headers, body=body, timeout=timeout)  # type: ignore[arg-type]


def test_sends_the_request_and_reads_the_answer() -> None:
    with local_server(lambda _: json_answer(201, {"data": {"id": "msg_1"}}, {"X-Trace-Id": "trace"})) as server:
        response = UrllibTransport().send(
            request(f"{server.url}/api/v1/messages", "POST", '{"body":"Bună ziua! Ștefan, țară"}')
        )

    received = server.received[0]
    assert (received.method, received.target) == ("POST", "/api/v1/messages")
    assert received.headers["authorization"] == "Bearer key"
    assert received.headers["content-type"] == "application/json"
    assert received.text == '{"body":"Bună ziua! Ștefan, țară"}'
    assert response.status == 201
    assert response.get_header("X-Trace-Id") == ["trace"]
    assert response.body == '{"data": {"id": "msg_1"}}'


def test_keeps_every_value_of_a_repeated_header() -> None:
    answer = Answer(200, b"{}", [("Vary", "Accept"), ("Vary", "Origin")])

    with local_server(lambda _: answer) as server:
        response = UrllibTransport().send(request(server.url))

    assert response.get_header("vary") == ["Accept", "Origin"]


@pytest.mark.parametrize("status", [400, 401, 404, 422, 429, 500, 503])
def test_returns_an_error_status_as_an_answer(status: int) -> None:
    with local_server(lambda _: json_answer(status, {"message": "Refused"}, {"X-Trace-Id": "trace"})) as server:
        response = UrllibTransport().send(request(server.url))

    assert response.status == status
    assert response.body == '{"message": "Refused"}'
    assert response.get_header_line("x-trace-id") == "trace"


def test_does_not_follow_a_redirect() -> None:
    def handle(received: object) -> Answer:
        return Answer(302, b"", {"Location": "/elsewhere"})

    with local_server(handle) as server:
        response = UrllibTransport().send(request(f"{server.url}/api/v1/messages"))

    assert response.status == 302
    assert response.get_header("Location") == ["/elsewhere"]
    assert [received.target for received in server.received] == ["/api/v1/messages"]


def test_gives_up_after_the_timeout_of_the_request() -> None:
    with local_server(lambda _: Answer(200, b"{}", delay=5)) as server:
        transport = UrllibTransport(timeout=30)

        with pytest.raises(TimeoutError, match=r"^Request timed out after 0\.2 s$"):
            transport.send(request(server.url, timeout=0.2))


def test_gives_up_after_its_own_timeout() -> None:
    with (
        local_server(lambda _: Answer(200, b"{}", delay=5)) as server,
        pytest.raises(TimeoutError, match=r"^Request timed out after 0\.2 s$"),
    ):
        UrllibTransport(timeout=0.2).send(request(server.url))


def test_reports_a_connection_that_timed_out_as_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = UrllibTransport(timeout=2)

    # urllib wraps the timeout of the connection in a URLError: a host that never answers
    def open_url(*args: object, **kwargs: object) -> object:
        raise urllib.error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr(transport._opener, "open", open_url)

    with pytest.raises(TimeoutError, match=r"^Request timed out after 2 s$") as caught:
        transport.send(request("https://rest.calisero.ro/api/v1/messages"))

    assert isinstance(caught.value.__cause__, urllib.error.URLError)


def test_raises_a_connection_error_when_the_connection_is_refused() -> None:
    # "Connection refused" on Linux and macOS, "... actively refused it" on Windows
    with pytest.raises(ConnectionError, match=r"[Rr]efused") as caught:
        UrllibTransport().send(request(f"http://127.0.0.1:{free_port()}/api/v1/messages"))

    assert caught.value.__cause__ is not None


def test_waits_30_seconds_by_default() -> None:
    assert UrllibTransport.DEFAULT_TIMEOUT == 30.0
    assert UrllibTransport().timeout == 30.0
    assert UrllibTransport(timeout=5).timeout == 5.0


@pytest.mark.parametrize(
    ("timeout", "error"),
    [(0, ValueError), (-1, ValueError), (float("inf"), ValueError), (float("nan"), ValueError), ("30", TypeError)],
)
def test_refuses_a_timeout_that_is_not_a_positive_number(timeout: object, error: type[Exception]) -> None:
    with pytest.raises(error, match=r"^The timeout must be a positive number of seconds, got "):
        UrllibTransport(timeout=timeout)  # type: ignore[arg-type]


def test_refuses_true_as_a_timeout() -> None:
    with pytest.raises(TypeError):
        UrllibTransport(timeout=True)


def test_sends_through_the_proxy_it_is_given() -> None:
    with local_server(lambda _: json_answer(200, {"data": []})) as proxy:
        response = UrllibTransport(proxy=proxy.url).send(request("http://calisero.invalid/api/v1/messages?page=2"))

    # A proxy gets the whole URL in the request line
    assert response.status == 200
    assert proxy.received[0].target == "http://calisero.invalid/api/v1/messages?page=2"


def test_sends_through_the_proxy_of_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    with local_server(lambda _: json_answer(200, {"data": []})) as proxy:
        # urllib prefers the lowercase spelling when both are set
        for name in ("http_proxy", "no_proxy", "NO_PROXY"):
            monkeypatch.delenv(name, raising=False)

        monkeypatch.setenv("HTTP_PROXY", proxy.url)

        UrllibTransport().send(request("http://calisero.invalid/api/v1/messages"))

    assert proxy.received[0].target == "http://calisero.invalid/api/v1/messages"


def test_uses_the_tls_settings_it_is_given() -> None:
    context = ssl.create_default_context()
    transport = UrllibTransport(ssl_context=context)

    # urllib's OpenerDirector keeps its handlers in an attribute it does not document
    handlers = transport._opener.handlers  # type: ignore[attr-defined]
    assert any(getattr(handler, "_context", None) is context for handler in handlers)
