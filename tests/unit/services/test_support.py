from __future__ import annotations

import pytest

from calisero import ApiError, HttpResponse, HttpResult, Message, OptOut
from calisero.services._support import page_query, path_id, read_page, read_single
from tests.support.fixtures import TRACE_ID, message_data, page_of


def result(body: object, status: int = 200, headers: dict[str, str] | None = None) -> HttpResult:
    return HttpResult(body=body, response=HttpResponse(status, headers or {}))


def test_read_single_reads_the_resource_and_the_headers() -> None:
    response = read_single(
        result({"data": message_data()}, 201, {"X-Trace-Id": TRACE_ID}), Message.from_dict, "message"
    )

    assert response.data.id == message_data()["id"]
    assert response.response_meta.trace_id == TRACE_ID


def test_read_page_reads_the_items_and_the_headers() -> None:
    page = read_page(result(page_of([], "opt-outs"), headers={"X-RateLimit-Remaining": "12"}), OptOut.from_dict)

    assert page.data == ()
    assert page.response_meta.rate_limit_remaining == 12


def test_read_page_turns_a_body_that_is_not_a_page_into_an_api_error() -> None:
    with pytest.raises(ApiError, match=r"^Unexpected API response: Invalid page: expected an object, got an array\.$"):
        read_page(result([]), OptOut.from_dict)


@pytest.mark.parametrize(("page", "query"), [(None, {}), (1, {}), (2, {"page": 2}), (50, {"page": 50})])
def test_page_query_sends_the_page_from_the_second_one_on(page: int | None, query: dict[str, int]) -> None:
    assert page_query(page) == query


@pytest.mark.parametrize(("value", "encoded"), [(TRACE_ID, TRACE_ID), ("a/b c", "a%2Fb%20c"), ("(x)!*'~", "(x)!*'~")])
def test_path_id_encodes_the_id_as_encode_uri_component_does(value: str, encoded: str) -> None:
    assert path_id(value, "message id") == encoded
