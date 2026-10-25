"""The library checked against the API's OpenAPI document.

resources/openApi/api-v1.json is the document published at https://docs.calisero.ro/open-api.
Every operation is implemented and reads the documented example answers, every documented
field is read or sent, and every documented error maps to its exception class.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

from calisero import (
    DEFAULT_BASE_URL,
    Account,
    ApiError,
    DailyLimitExceededError,
    DeliveryWebhookMessage,
    ForbiddenError,
    Message,
    NotFoundError,
    OptOut,
    PaginationLinks,
    PaginationMeta,
    ServerError,
    ShortenedLink,
    SmsClient,
    UnauthorizedError,
    ValidationError,
    Verification,
)
from calisero._payloads import (
    create_message_payload,
    create_verification_payload,
    opt_out_payload,
    verification_check_payload,
)
from tests.support.stub_transport import client_answering, json_response, request_body

SPEC: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "resources" / "openApi" / "api-v1.json").read_text(encoding="utf-8")
)

ID = "019a62f1-66b7-7387-a64f-2742c12a2860"
PHONE = "+40742***350"

# How the library calls each operation of the API, by operationId, and the query it sends
CALLS: dict[str, tuple[Callable[[SmsClient], object], str]] = {
    "getAccount": (lambda client: client.accounts.get(ID), ""),
    "createMessage": (
        lambda client: client.messages.create(
            recipient=PHONE,
            body="Test message",
            visible_body="Test ******",
            validity=72,
            schedule_at="2026-11-16 13:21:00",
            callback_url="https://yoursite.com/your-callback-url",
            sender="CALISERO",
            shorten_urls=True,
        ),
        "",
    ),
    "listMessages": (lambda client: client.messages.list(page=2), "page=2"),
    "getMessage": (lambda client: client.messages.get(ID), ""),
    "deleteMessage": (lambda client: client.messages.delete(ID), ""),
    "listOptOuts": (lambda client: client.opt_outs.list(page=2), "page=2"),
    "createOptOut": (lambda client: client.opt_outs.create(phone=PHONE, reason="Unsubscribed"), ""),
    "getOptOut": (lambda client: client.opt_outs.get(ID), ""),
    "updateOptOut": (lambda client: client.opt_outs.update(ID, phone=PHONE, reason="Unsubscribed"), ""),
    "deleteOptOut": (lambda client: client.opt_outs.delete(ID), ""),
    "listVerifications": (
        lambda client: client.verifications.list(page=2, status="verified"),
        "page=2&status=verified",
    ),
    "createVerification": (
        lambda client: client.verifications.create(
            phone=PHONE, brand="Calisero", template="Code: {code}", expires_in=5
        ),
        "",
    ),
    "getVerification": (lambda client: client.verifications.get(ID), ""),
    "validateVerificationPost": (lambda client: client.verifications.validate(phone=PHONE, code="SBMH0f"), ""),
}

ERROR_CLASSES: dict[str, type[ApiError]] = {
    "401": UnauthorizedError,
    "403": ForbiddenError,
    "404": NotFoundError,
    "405": ApiError,
    "422": ValidationError,
    "429": DailyLimitExceededError,
    "500": ServerError,
}


def resolve(value: dict[str, Any]) -> dict[str, Any]:
    reference = value.get("$ref")

    if reference is None:
        return value

    _, _, section, name = reference.split("/")

    return resolve(SPEC["components"][section][name])


def media_of(response: dict[str, Any]) -> dict[str, Any]:
    media: dict[str, Any] = resolve(response).get("content", {}).get("application/json", {})

    return media


def examples_of(response: dict[str, Any]) -> list[Any]:
    media = media_of(response)

    if "example" in media:
        return [media["example"]]

    return [example["value"] for example in media.get("examples", {}).values()]


def success_examples(response: dict[str, Any]) -> list[Any]:
    """The examples of a successful answer; for one documented by its schema alone, those of the others with it."""
    own = examples_of(response)
    schema = media_of(response).get("schema", {}).get("$ref")

    if own or schema is None:
        return own

    return [
        example
        for methods in SPEC["paths"].values()
        for operation in methods.values()
        for other in operation.get("responses", {}).values()
        if media_of(other).get("schema", {}).get("$ref") == schema
        for example in examples_of(other)
    ]


def properties_of(schema_name: str) -> list[str]:
    return list(resolve(SPEC["components"]["schemas"][schema_name]).get("properties", {}))


def snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def success_of(operation: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    status, response = next((code, answer) for code, answer in operation["responses"].items() if code.startswith("2"))

    return int(status), response


# The API's operations. The delivery webhook, which Calisero sends rather than answers, is a callback of
# POST /messages, not one of them
DOCUMENTED_OPERATIONS: list[tuple[str, str, dict[str, Any]]] = [
    (path, method.upper(), operation)
    for path, methods in SPEC["paths"].items()
    for method, operation in methods.items()
]

DELIVERY_WEBHOOK: dict[str, Any] = SPEC["paths"]["/messages"]["post"]["callbacks"]["deliveryStatus"][
    "{$request.body#/callback_url}"
]["post"]

OPERATIONS = [pytest.param(*operation, id=f"{operation[1]} {operation[0]}") for operation in DOCUMENTED_OPERATIONS]


def test_the_document_is_the_version_this_library_was_built_for() -> None:
    assert re.match(r"^1\.0\.15\b", SPEC["info"]["version"])
    assert SPEC["servers"][0]["url"] == DEFAULT_BASE_URL


def test_the_document_has_no_operation_the_library_lacks_and_the_library_calls_none_it_does_not_document() -> None:
    documented = sorted(operation["operationId"] for _, _, operation in DOCUMENTED_OPERATIONS)

    assert documented == sorted(CALLS)


@pytest.mark.parametrize(("path", "method", "operation"), OPERATIONS)
def test_is_called_with_the_documented_method_path_and_query(path: str, method: str, operation: dict[str, Any]) -> None:
    call, query = CALLS[operation["operationId"]]
    status, success = success_of(operation)
    client, transport = client_answering(json_response(status, success_examples(success)[0]))

    call(client)

    url = urlsplit(transport.last_request.url)
    assert transport.last_request.method == method
    assert url.path == "/api/v1" + re.sub(r"\{[^}]+\}", ID, path)
    assert url.query == query


@pytest.mark.parametrize(("path", "method", "operation"), OPERATIONS)
def test_reads_the_documented_answers(path: str, method: str, operation: dict[str, Any]) -> None:
    call, _ = CALLS[operation["operationId"]]
    status, success = success_of(operation)
    examples = success_examples(success)

    assert examples, f"No example documented for {method} {path}"

    for example in examples:
        client, _ = client_answering(json_response(status, example))

        # Raises, failing the test, when the library cannot read the example
        call(client)


@pytest.mark.parametrize(
    ("path", "method", "operation"),
    [
        pytest.param(*operation, id=f"{operation[1]} {operation[0]}")
        for operation in DOCUMENTED_OPERATIONS
        if "requestBody" in operation[2]
    ],
)
def test_sends_only_documented_fields_the_required_ones_included(
    path: str, method: str, operation: dict[str, Any]
) -> None:
    call, _ = CALLS[operation["operationId"]]
    schema = resolve(operation["requestBody"]["content"]["application/json"]["schema"])
    status, success = success_of(operation)
    client, transport = client_answering(json_response(status, success_examples(success)[0]))

    call(client)

    sent = request_body(transport.last_request)
    assert isinstance(sent, dict)
    assert set(sent) <= set(schema["properties"])
    assert set(schema.get("required", [])) <= set(sent)


def documented_answer(path: str, method: str, status: str) -> Any:
    """The first documented example of an answer."""
    examples = examples_of(SPEC["paths"][path][method]["responses"][status])

    assert examples, f"No example documented for the {status} answer of {method.upper()} {path}"

    return examples[0]


@pytest.mark.parametrize(
    ("schema_name", "read"),
    [
        ("Message", lambda: Message.from_dict(documented_answer("/messages", "post", "201")["data"])),
        (
            "ShortenedLink",
            lambda: ShortenedLink.from_dict(documented_answer("/messages", "post", "201")["data"]["shortened_urls"][0]),
        ),
        ("OptOut", lambda: OptOut.from_dict(documented_answer("/opt-outs", "post", "201")["data"])),
        ("Account", lambda: Account.from_dict(documented_answer("/accounts/{accountId}", "get", "200")["data"])),
        ("Verification", lambda: Verification.from_dict(documented_answer("/verifications", "post", "201")["data"])),
    ],
)
def test_every_documented_field_of_a_resource_is_read(schema_name: str, read: Callable[[], object]) -> None:
    model = read()

    for name in properties_of(schema_name):
        assert hasattr(model, name), f"{schema_name}.{name}"


def test_every_documented_field_of_the_pagination_is_read() -> None:
    page = documented_answer("/messages", "get", "200")
    links = PaginationLinks.from_dict(page["links"])
    meta = PaginationMeta.from_dict(page["meta"])
    schema = resolve(SPEC["components"]["schemas"]["PaginatedMessages"])

    for name in schema["properties"]["links"]["properties"]:
        assert hasattr(links, name), f"links.{name}"

    # `from` is a Python keyword: the attribute is `from_`
    for name in schema["properties"]["meta"]["properties"]:
        assert hasattr(meta, "from_" if name == "from" else name), f"meta.{name}"


def test_the_documented_delivery_webhook_payload_is_read_every_field_of_it() -> None:
    example = DELIVERY_WEBHOOK["requestBody"]["content"]["application/json"]["example"]

    message = DeliveryWebhookMessage.from_dict(example)

    for name in properties_of("DeliveryWebhookMessage"):
        assert getattr(message, snake_case(name)) == example[name], name


@pytest.mark.parametrize(
    ("schema_name", "payload"),
    [
        (
            "CreateMessageRequest",
            create_message_payload(
                recipient=PHONE,
                body="b",
                visible_body="v",
                validity=1,
                schedule_at=datetime.now(timezone.utc),
                callback_url="https://yoursite.com",
                sender="s",
                shorten_urls=True,
            ),
        ),
        ("CreateOptOutRequest", opt_out_payload(phone=PHONE, reason="r")),
        ("UpdateOptOutRequest", opt_out_payload(phone=PHONE, reason="r")),
        (
            "CreateVerificationRequest",
            create_verification_payload(phone=PHONE, brand="b", template="{code}", expires_in=5),
        ),
        ("VerificationCheckRequest", verification_check_payload(phone=PHONE, code="ABC123")),
    ],
)
def test_the_library_can_send_every_documented_field_of_a_request(schema_name: str, payload: dict[str, object]) -> None:
    assert sorted(payload) == sorted(properties_of(schema_name))


DOCUMENTED_ERRORS: list[tuple[str, str, Any]] = [
    (operation["operationId"], status, example)
    for _, _, operation in DOCUMENTED_OPERATIONS
    for status, response in operation.get("responses", {}).items()
    if not status.startswith("2")
    for example in examples_of(response)
]


def test_every_documented_error_status_is_mapped() -> None:
    assert {status for _, status, _ in DOCUMENTED_ERRORS} == set(ERROR_CLASSES)


@pytest.mark.parametrize(
    ("operation_id", "status", "example"),
    [pytest.param(*error, id=f"{error[0]} {error[1]}") for error in DOCUMENTED_ERRORS],
)
def test_a_documented_error_raises_its_exception_with_its_message(
    operation_id: str, status: str, example: dict[str, Any]
) -> None:
    call, _ = CALLS[operation_id]
    client, _ = client_answering(json_response(int(status), example))

    with pytest.raises(ApiError) as caught:
        call(client)

    assert type(caught.value) is ERROR_CLASSES[status]
    assert caught.value.status_code == int(status)
    assert caught.value.message == example["message"]
