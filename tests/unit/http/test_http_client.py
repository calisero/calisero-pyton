from __future__ import annotations

import json

import pytest

from calisero import VERSION, ApiError, AppInfo, HttpClient, HttpResponse, TransportError, UrllibTransport
from calisero.http.user_agent import RUNTIME
from tests.support.fixtures import TRACE_ID
from tests.support.stub_transport import StaticToken, StubTransport, http_client_answering, json_response

BASE = "https://rest.calisero.ro/api/v1"
RUNTIME_COMMENT = f"({RUNTIME.implementation} {RUNTIME.version}; {RUNTIME.system} {RUNTIME.machine})"


class TestRequests:
    def test_sends_a_get_with_the_standard_headers_and_no_body(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {"data": []}))

        http_client.get("/messages")

        request = transport.last_request
        assert request.method == "GET"
        assert request.url == f"{BASE}/messages"
        assert dict(request.headers) == {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"Calisero-SMS-Python/{VERSION} {RUNTIME_COMMENT}",
            "Authorization": "Bearer test-api-key",
        }
        assert request.body is None
        assert request.timeout is None

    def test_hides_the_api_key_when_a_request_is_printed(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {"data": []}))

        http_client.get("/messages")

        assert "test-api-key" not in repr(transport.last_request)
        assert "'Authorization': 'Bearer ***'" in repr(transport.last_request)

    def test_names_the_library_its_version_and_the_runtime_in_every_request(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {}), json_response(201, {}))

        http_client.get("/messages")
        http_client.post("/messages", {"recipient": "+40742***350", "body": "Hello"})

        assert http_client.user_agent == f"Calisero-SMS-Python/{VERSION} {RUNTIME_COMMENT}"
        assert [request.headers["User-Agent"] for request in transport.requests] == [http_client.user_agent] * 2

    def test_names_your_application_after_the_library(self) -> None:
        transport = StubTransport(json_response(200, {}))
        http_client = HttpClient(StaticToken(), transport=transport, app_info=AppInfo(name="MyShop", version="2.1.0"))

        http_client.get("/messages")

        assert transport.last_request.headers["User-Agent"] == (
            f"Calisero-SMS-Python/{VERSION} {RUNTIME_COMMENT} MyShop/2.1.0"
        )

    def test_refuses_an_application_without_a_usable_name(self) -> None:
        with pytest.raises(ValueError, match=r"^app_info\.name must name your application"):
            HttpClient(StaticToken(), app_info=AppInfo(name="  "))

    def test_adds_the_query_parameters_it_is_given_leaving_out_none(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {}), json_response(200, {}))

        http_client.get("/verifications", {"page": 2, "status": "verified", "skipped": None})
        http_client.get("/verifications", {"skipped": None})

        assert transport.requests[0].url == f"{BASE}/verifications?page=2&status=verified"
        assert transport.requests[1].url == f"{BASE}/verifications"

    def test_writes_booleans_as_the_api_reads_them(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {}))

        http_client.get("/messages", {"yes": True, "no": False, "ratio": 1.5})

        assert transport.last_request.url == f"{BASE}/messages?yes=true&no=false&ratio=1.5"

    def test_encodes_the_query_parameters(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {}))

        http_client.get("/messages", {"q": "a b&c=d"})

        assert transport.last_request.url == f"{BASE}/messages?q=a+b%26c%3Dd"

    def test_sends_a_post_with_a_json_body(self) -> None:
        http_client, transport = http_client_answering(json_response(201, {"data": {"id": "msg_1"}}))

        result = http_client.post("/messages", {"recipient": "+40742***350", "body": "Bună ziua!"})

        assert transport.last_request.method == "POST"
        assert transport.last_request.url == f"{BASE}/messages"
        assert transport.last_request.body == '{"recipient":"+40742***350","body":"Bună ziua!"}'
        assert result.body == {"data": {"id": "msg_1"}}
        assert result.response.status == 201

    def test_sends_a_post_without_data_without_a_body(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {}), json_response(200, {}))

        http_client.post("/messages")
        http_client.post("/messages", {})

        assert [request.body for request in transport.requests] == [None, None]

    def test_refuses_data_that_is_not_json_before_sending(self) -> None:
        http_client, transport = http_client_answering()

        with pytest.raises(ValueError, match="not JSON compliant"):
            http_client.post("/messages", {"validity": float("nan")})

        assert transport.requests == []

    def test_sends_a_put_with_a_json_body(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {"data": {}}))

        http_client.put("/verifications/validate", {"phone": "+40742***350", "code": "ABC123"})

        assert transport.last_request.method == "PUT"
        assert transport.last_request.body == '{"phone":"+40742***350","code":"ABC123"}'

    def test_sends_a_delete_without_a_body_and_reads_its_answer(self) -> None:
        # The API answers a delete with 200 and an empty JSON array
        http_client, transport = http_client_answering(json_response(200, []))

        result = http_client.delete("/messages/msg_1")

        assert transport.last_request.method == "DELETE"
        assert transport.last_request.url == f"{BASE}/messages/msg_1"
        assert transport.last_request.body is None
        assert result.body == []

    def test_reads_an_answer_without_a_body_as_none(self) -> None:
        http_client, _ = http_client_answering(HttpResponse(204, {}, ""))

        assert http_client.delete("/opt-outs/opt_1").body is None

    def test_joins_the_base_url_and_the_path_with_a_single_slash(self) -> None:
        transport = StubTransport(json_response(200, {}), json_response(200, {}))
        http_client = HttpClient(StaticToken(), transport=transport, base_url=f"{BASE}//")

        http_client.get("messages")
        http_client.get("//messages")

        assert http_client.base_url == BASE
        assert [request.url for request in transport.requests] == [f"{BASE}/messages", f"{BASE}/messages"]

    @pytest.mark.parametrize(
        "base_url", ["", "rest.calisero.ro/api/v1", "ftp://rest.calisero.ro", "file:///etc/passwd", "https://"]
    )
    def test_refuses_a_base_url_that_is_not_an_http_url(self, base_url: str) -> None:
        with pytest.raises(ValueError, match=r"^The base URL must be an http:// or https:// URL"):
            HttpClient(StaticToken(), base_url=base_url)

    def test_passes_the_timeout_of_a_call_to_the_transport(self) -> None:
        http_client, transport = http_client_answering(json_response(200, {}))

        http_client.get("/messages", timeout=2.5)

        assert transport.last_request.timeout == 2.5

    @pytest.mark.parametrize(("timeout", "error"), [(0, ValueError), (-1, ValueError), ("5", TypeError)])
    def test_refuses_a_timeout_that_is_not_positive_before_sending(
        self, timeout: object, error: type[Exception]
    ) -> None:
        http_client, transport = http_client_answering()

        with pytest.raises(error, match="The timeout must be a positive number of seconds"):
            http_client.get("/messages", timeout=timeout)  # type: ignore[arg-type]

        assert transport.requests == []

    def test_lets_an_auth_provider_error_through_without_sending_the_request(self) -> None:
        class Unreachable:
            def get_token(self) -> str:
                raise ConnectionError("Vault unreachable")

        transport = StubTransport()
        http_client = HttpClient(Unreachable(), transport=transport)

        with pytest.raises(ConnectionError, match="Vault unreachable"):
            http_client.get("/messages")

        assert transport.requests == []

    def test_refuses_a_token_a_header_cannot_carry_without_sending_or_showing_it(self) -> None:
        transport = StubTransport()
        http_client = HttpClient(StaticToken("secret\r\nX-Injected: yes"), transport=transport)

        with pytest.raises(ValueError, match="must hold only visible ASCII characters") as caught:
            http_client.get("/messages")

        assert "secret" not in str(caught.value)
        assert transport.requests == []

    def test_sends_no_idempotency_key_the_api_takes_none(self) -> None:
        http_client, transport = http_client_answering(json_response(201, {}))

        http_client.post("/messages", {"recipient": "+40742***350", "body": "Hello"})

        assert "Idempotency-Key" not in transport.last_request.headers

    def test_sends_through_urllib_to_the_production_api_by_default(self) -> None:
        http_client = HttpClient(StaticToken())

        assert http_client.base_url == BASE
        assert isinstance(http_client._transport, UrllibTransport)


class TestAnswers:
    def test_decodes_a_json_answer(self) -> None:
        http_client, _ = http_client_answering(json_response(200, {"data": {"id": "msg_1", "parts": 2}}))

        assert http_client.get("/messages/msg_1").body == {"data": {"id": "msg_1", "parts": 2}}

    def test_refuses_a_successful_answer_that_is_not_json(self) -> None:
        http_client, _ = http_client_answering(HttpResponse(200, {"X-Trace-Id": TRACE_ID}, "<html>OK</html>"))

        with pytest.raises(ApiError, match=r"^Failed to decode JSON response: ") as caught:
            http_client.get("/messages")

        assert type(caught.value) is ApiError
        assert caught.value.status_code == 200
        assert caught.value.trace_id == TRACE_ID
        assert isinstance(caught.value.__cause__, json.JSONDecodeError)

    def test_refuses_nan_which_is_not_json(self) -> None:
        http_client, _ = http_client_answering(HttpResponse(200, {}, '{"credit": NaN}'))

        with pytest.raises(ApiError, match="NaN is not valid JSON"):
            http_client.get("/messages")


def last_response_of(http_client: HttpClient) -> HttpResponse | None:
    # Read through a function: the type checker would otherwise keep what an earlier assertion narrowed
    return http_client.last_response


class TestLastResponse:
    def test_keeps_the_answer_of_every_request(self) -> None:
        success = json_response(201, {"data": {"id": "msg_1"}}, {"X-Trace-Id": TRACE_ID})
        failure = json_response(404, {"message": "Resource not found!"})
        http_client, _ = http_client_answering(success, failure)

        assert last_response_of(http_client) is None

        http_client.post("/messages", {"recipient": "+40742***350", "body": "Hello"})
        assert last_response_of(http_client) is success

        with pytest.raises(ApiError, match="Resource not found!"):
            http_client.get("/messages/missing")

        assert last_response_of(http_client) is failure

    def test_is_cleared_when_a_request_gets_no_answer(self) -> None:
        http_client, _ = http_client_answering(json_response(200, {"data": []}), TimeoutError("Connection timed out"))

        http_client.get("/messages")
        assert last_response_of(http_client) is not None

        with pytest.raises(TransportError):
            http_client.get("/messages")

        assert last_response_of(http_client) is None
