from __future__ import annotations

import ssl

import pytest

from calisero import (
    VERSION,
    AccountService,
    AppInfo,
    BearerTokenAuthProvider,
    HttpClient,
    MessageService,
    OptOutService,
    SmsClient,
    UrllibTransport,
    VerificationService,
)
from tests.support.fixtures import message_data
from tests.support.stub_transport import StaticToken, StubTransport, json_response


def transport_of(client: SmsClient) -> object:
    return client.http_client._transport


def test_create_gives_the_services_on_one_http_client() -> None:
    client = SmsClient.create("test-api-key")

    assert isinstance(client.messages, MessageService)
    assert isinstance(client.opt_outs, OptOutService)
    assert isinstance(client.accounts, AccountService)
    assert isinstance(client.verifications, VerificationService)
    assert isinstance(client.http_client, HttpClient)

    for service in (client.messages, client.opt_outs, client.accounts, client.verifications):
        assert service._http_client is client.http_client


def test_create_gives_independent_clients() -> None:
    first, second = SmsClient.create("key-1"), SmsClient.create("key-2")

    assert first.http_client is not second.http_client
    assert transport_of(first) is not transport_of(second)


def test_create_talks_to_the_production_api_through_urllib_by_default() -> None:
    client = SmsClient.create("test-api-key")
    transport = transport_of(client)

    assert client.http_client.base_url == "https://rest.calisero.ro/api/v1"
    assert isinstance(transport, UrllibTransport)
    assert transport.timeout == 30.0


def test_create_sends_the_api_key_as_a_bearer_token() -> None:
    transport = StubTransport(json_response(200, {"data": message_data()}))
    client = SmsClient.create("  secret-key\n", transport=transport)

    client.messages.get("msg_1")

    # A key read from a file or an environment variable loses its newline
    assert transport.last_request.headers["Authorization"] == "Bearer secret-key"


@pytest.mark.parametrize(
    ("api_key", "error"),
    [
        (None, TypeError),
        (42, TypeError),
        ("", ValueError),
        ("   ", ValueError),
    ],
)
def test_create_refuses_a_missing_or_empty_api_key(api_key: object, error: type[Exception]) -> None:
    with pytest.raises(error, match=r"^The API key must be a non-empty string\.$"):
        SmsClient.create(api_key)  # type: ignore[arg-type]


def test_create_refuses_an_api_key_a_header_cannot_carry_without_showing_it() -> None:
    with pytest.raises(ValueError, match=r"^The API key must hold only visible ASCII characters\.$") as caught:
        SmsClient.create("secret key")

    assert "secret" not in str(caught.value)


def test_create_reads_the_token_of_an_auth_provider_before_each_request() -> None:
    class RotatingToken:
        def __init__(self) -> None:
            self.calls = 0

        def get_token(self) -> str:
            self.calls += 1

            return f"key-{self.calls}"

    provider = RotatingToken()
    transport = StubTransport(
        json_response(200, {"data": message_data()}),
        json_response(200, {"data": message_data()}),
    )
    client = SmsClient.create(provider, transport=transport)

    client.messages.get("msg_1")
    client.messages.get("msg_1")

    assert [request.headers["Authorization"] for request in transport.requests] == ["Bearer key-1", "Bearer key-2"]


def test_create_takes_a_base_url() -> None:
    transport = StubTransport(json_response(200, {"data": message_data()}))
    client = SmsClient.create("test-api-key", base_url="https://sandbox.example.test/api/v1/", transport=transport)

    client.messages.get("msg_1")

    assert transport.last_request.url == "https://sandbox.example.test/api/v1/messages/msg_1"


def test_create_names_your_application_in_the_user_agent() -> None:
    client = SmsClient.create("test-api-key", app_info=AppInfo("MyShop", "2.1.0"))

    assert client.http_client.user_agent.startswith(f"Calisero-SMS-Python/{VERSION} (")
    assert client.http_client.user_agent.endswith(") MyShop/2.1.0")


def test_create_takes_a_timeout() -> None:
    transport = transport_of(SmsClient.create("test-api-key", timeout=5))

    assert isinstance(transport, UrllibTransport)
    assert transport.timeout == 5.0


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_create_refuses_a_timeout_that_is_not_positive(timeout: float) -> None:
    with pytest.raises(ValueError, match="The timeout must be a positive number of seconds"):
        SmsClient.create("test-api-key", timeout=timeout)


def test_create_takes_a_proxy_and_tls_settings() -> None:
    context = ssl.create_default_context()
    proxy = "http://proxy.internal:3128"
    transport = transport_of(SmsClient.create("test-api-key", proxy=proxy, ssl_context=context))

    assert isinstance(transport, UrllibTransport)
    # urllib's OpenerDirector keeps its handlers in an attribute it does not document
    handlers = transport._opener.handlers  # type: ignore[attr-defined]
    assert any(getattr(handler, "proxies", None) == {"http": proxy, "https": proxy} for handler in handlers)
    assert any(getattr(handler, "_context", None) is context for handler in handlers)


def test_create_uses_the_transport_it_is_given_and_ignores_the_timeout() -> None:
    transport = StubTransport()
    client = SmsClient.create("test-api-key", transport=transport, timeout=1)

    assert transport_of(client) is transport


def test_a_client_on_an_http_client_built_by_hand() -> None:
    transport = StubTransport(json_response(200, {"data": message_data()}))
    http_client = HttpClient(BearerTokenAuthProvider("hand-made"), transport=transport)
    client = SmsClient(http_client)

    client.messages.get("msg_1")

    assert client.http_client is http_client
    assert transport.last_request.headers["Authorization"] == "Bearer hand-made"
    assert http_client.last_response is not None


def test_an_auth_provider_is_any_object_with_get_token() -> None:
    transport = StubTransport(json_response(200, {"data": message_data()}))

    SmsClient.create(StaticToken("from-vault"), transport=transport).messages.get("msg_1")

    assert transport.last_request.headers["Authorization"] == "Bearer from-vault"


def test_the_version_is_on_the_class() -> None:
    assert SmsClient.VERSION == VERSION
