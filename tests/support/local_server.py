"""HTTP servers on free local ports: the tests talk to them over real sockets, never to the network."""

from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

if TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication


@dataclass(frozen=True)
class ReceivedRequest:
    """A request the server received."""

    method: str

    #: The request target: the path and the query string, or the whole URL of a request sent to a proxy.
    target: str

    #: The headers, their names in lowercase.
    headers: dict[str, str]

    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8")


@dataclass(frozen=True)
class Answer:
    """What the server answers."""

    status: int
    body: bytes | str = b""
    headers: Mapping[str, str] | list[tuple[str, str]] = field(default_factory=dict)

    #: Seconds to wait before answering, cut short when the server closes.
    delay: float = 0.0


def json_answer(status: int, body: object, headers: Mapping[str, str] | None = None) -> Answer:
    return Answer(status, json.dumps(body), {"Content-Type": "application/json", **(headers or {})})


Handler = Callable[[ReceivedRequest], Answer]


class LocalServer:
    """An HTTP server running `handle` for every request, in a thread of its own."""

    def __init__(self, handle: Handler) -> None:
        self.received: list[ReceivedRequest] = []
        self.stopping = threading.Event()
        self._server = _ThreadingServer(("127.0.0.1", 0), _request_handler(self, handle))
        self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05})

    @property
    def url(self) -> str:
        """The server's base URL, e.g. http://127.0.0.1:53412"""
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        # Delayed answers stop waiting, then every request thread is joined
        self.stopping.set()
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()


@contextmanager
def local_server(handle: Handler) -> Iterator[LocalServer]:
    server = LocalServer(handle)
    server.start()

    try:
        yield server
    finally:
        server.close()


class _ThreadingServer(ThreadingHTTPServer):
    # Request threads are joined when the server closes, so none outlives a test
    daemon_threads = False
    block_on_close = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        # A client that gave up before its answer (the timeout tests): nothing to report
        pass


def _request_handler(server: LocalServer, handle: Handler) -> type[BaseHTTPRequestHandler]:
    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._serve()

        def do_POST(self) -> None:
            self._serve()

        def do_PUT(self) -> None:
            self._serve()

        def do_DELETE(self) -> None:
            self._serve()

        def _serve(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            request = ReceivedRequest(
                method=self.command,
                target=self.path,
                headers={name.lower(): value for name, value in self.headers.items()},
                body=self.rfile.read(length) if length else b"",
            )
            server.received.append(request)
            answer = handle(request)

            if answer.delay and server.stopping.wait(answer.delay):
                return

            content = answer.body.encode("utf-8") if isinstance(answer.body, str) else answer.body
            headers = answer.headers.items() if isinstance(answer.headers, Mapping) else answer.headers

            self.send_response(answer.status)

            for name, value in headers:
                self.send_header(name, value)

            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    return RequestHandler


class WsgiServer:
    """A WSGI application served over HTTP, e.g. the webhook handler."""

    def __init__(self, app: WSGIApplication) -> None:
        self._server: WSGIServer = make_server("127.0.0.1", 0, app, handler_class=_QuietWsgiHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05})

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()


@contextmanager
def wsgi_server(app: WSGIApplication) -> Iterator[WsgiServer]:
    server = WsgiServer(app)
    server._thread.start()

    try:
        yield server
    finally:
        server.close()


class _QuietWsgiHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


@dataclass(frozen=True)
class Reply:
    """An answer received by `send()`."""

    status: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body)


def send(method: str, url: str, body: bytes | None = None, headers: Mapping[str, str] | None = None) -> Reply:
    """Send a request with urllib and read the answer, whatever its status."""
    request = urllib.request.Request(url, data=body, headers=dict(headers or {}), method=method)  # noqa: S310

    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            return Reply(response.status, {k.lower(): v for k, v in response.headers.items()}, response.read())
    except urllib.error.HTTPError as error:
        with error:
            return Reply(error.code, {k.lower(): v for k, v in error.headers.items()}, error.read())


def free_port() -> int:
    """A local port nothing listens on: connecting to it is refused."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))

        return int(probe.getsockname()[1])
