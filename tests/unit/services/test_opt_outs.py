from __future__ import annotations

from collections.abc import Callable

import pytest

from calisero import NotFoundError, OptOut, SmsClient, ValidationError
from tests.support.fixtures import OPT_OUT_ID, PHONE, opt_out_data, page_of
from tests.support.stub_transport import client_answering, json_response, request_body

BASE = "https://rest.calisero.ro/api/v1"


def test_create_opts_a_number_out_with_a_reason() -> None:
    client, transport = client_answering(json_response(201, {"data": opt_out_data()}))

    response = client.opt_outs.create(phone=PHONE, reason="Customer asked to stop receiving messages")

    assert (transport.last_request.method, transport.last_request.url) == ("POST", f"{BASE}/opt-outs")
    assert request_body(transport.last_request) == {
        "phone": PHONE,
        "reason": "Customer asked to stop receiving messages",
    }
    assert response.data == OptOut.from_dict(opt_out_data())


def test_create_opts_a_number_out_without_a_reason() -> None:
    client, transport = client_answering(json_response(201, {"data": opt_out_data(reason=None)}))

    response = client.opt_outs.create(phone=PHONE)

    assert request_body(transport.last_request) == {"phone": PHONE}
    assert response.data.reason is None


def test_create_raises_the_refusal_of_a_number_already_opted_out() -> None:
    body = {"message": "The phone has already been taken.", "errors": {"phone": ["The phone has already been taken."]}}
    client, _ = client_answering(json_response(422, body))

    with pytest.raises(ValidationError) as caught:
        client.opt_outs.create(phone=PHONE)

    assert list(caught.value.validation_errors) == ["phone"]


def test_get_retrieves_an_opt_out() -> None:
    client, transport = client_answering(json_response(200, {"data": opt_out_data()}))

    response = client.opt_outs.get(OPT_OUT_ID)

    assert (transport.last_request.method, transport.last_request.url) == ("GET", f"{BASE}/opt-outs/{OPT_OUT_ID}")
    assert response.data.id == OPT_OUT_ID


def test_get_raises_not_found() -> None:
    client, _ = client_answering(json_response(404, {"message": "Resource not found!"}))

    with pytest.raises(NotFoundError):
        client.opt_outs.get(OPT_OUT_ID)


def test_list_reads_the_page_it_is_asked_for() -> None:
    client, transport = client_answering(json_response(200, page_of([opt_out_data()], "opt-outs", 3)))

    page = client.opt_outs.list(page=3)

    assert transport.last_request.url == f"{BASE}/opt-outs?page=3"
    assert [opt_out.id for opt_out in page] == [OPT_OUT_ID]
    assert page.meta.current_page == 3


def test_update_sends_the_new_data() -> None:
    client, transport = client_answering(json_response(200, {"data": opt_out_data(reason="Updated reason")}))

    response = client.opt_outs.update(OPT_OUT_ID, phone=PHONE, reason="Updated reason")

    assert (transport.last_request.method, transport.last_request.url) == ("PUT", f"{BASE}/opt-outs/{OPT_OUT_ID}")
    assert request_body(transport.last_request) == {"phone": PHONE, "reason": "Updated reason"}
    assert response.data.reason == "Updated reason"


def test_delete_removes_an_opt_out() -> None:
    client, transport = client_answering(json_response(200, []))

    client.opt_outs.delete(OPT_OUT_ID, timeout=4)

    assert (transport.last_request.method, transport.last_request.url) == ("DELETE", f"{BASE}/opt-outs/{OPT_OUT_ID}")
    assert transport.last_request.timeout == 4


@pytest.mark.parametrize(
    "call",
    [
        lambda client: client.opt_outs.get(""),
        lambda client: client.opt_outs.update("", phone=PHONE),
        lambda client: client.opt_outs.delete(" "),
    ],
    ids=["get", "update", "delete"],
)
def test_refuses_an_empty_id_before_sending(call: Callable[[SmsClient], object]) -> None:
    client, transport = client_answering()

    with pytest.raises(ValueError, match=r"^The opt-out id must be a non-empty string\.$"):
        call(client)

    assert transport.requests == []
