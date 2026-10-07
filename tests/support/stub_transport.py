"""A transport that answers from a queue: the services are tested without the network."""

from __future__ import annotations

import json
from typing import Final, TypeAlias

from calisero import HttpClient, HttpRequest, HttpResponse, SmsClient

#: An answer of the stub: a response, or the exception of a request that got none.
StubAnswer: TypeAlias = HttpResponse | BaseException

#: The body of an answer that has none.
NO_BODY: Final = object()


class StubTransport:
    """A transport that records its requests and gives the queued answers in turn."""

    def __init__(self, *answers: StubAnswer) -> None:
        self.requests: list[HttpRequest] = []
        self._answers = list(answers)

    @property
    def last_request(self) -> HttpRequest:
        if not self.requests:
            raise AssertionError("StubTransport: no request was sent")

        return self.requests[-1]

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)

        if not self._answers:
            raise AssertionError(f"StubTransport: no answer queued for {request.method} {request.url}")

        answer = self._answers.pop(0)

        if isinstance(answer, BaseException):
            raise answer

        return answer


def json_response(status: int, body: object = NO_BODY, headers: dict[str, str] | None = None) -> HttpResponse:
    """A JSON answer, as the API sends them."""
    return HttpResponse(
        status,
        {"Content-Type": "application/json", **(headers or {})},
        "" if body is NO_BODY else json.dumps(body),
    )


def client_answering(*answers: StubAnswer) -> tuple[SmsClient, StubTransport]:
    """A client whose requests get the given answers in turn."""
    transport = StubTransport(*answers)

    return SmsClient.create("test-api-key", transport=transport), transport


class StaticToken:
    """An auth provider giving a fixed token."""

    def __init__(self, token: str = "test-api-key") -> None:
        self.token = token

    def get_token(self) -> str:
        return self.token


def http_client_answering(*answers: StubAnswer) -> tuple[HttpClient, StubTransport]:
    """An HTTP client whose requests get the given answers in turn."""
    transport = StubTransport(*answers)

    return HttpClient(StaticToken(), transport=transport), transport


def request_body(request: HttpRequest) -> object:
    """The decoded JSON body of a request."""
    return None if request.body is None else json.loads(request.body)
