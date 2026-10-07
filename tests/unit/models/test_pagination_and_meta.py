from __future__ import annotations

import pytest

from calisero import (
    ApiResponse,
    HttpResponse,
    Message,
    OptOut,
    Paginated,
    PaginationLinks,
    PaginationMeta,
    ResponseMeta,
)
from tests.support.fixtures import MESSAGE_ID, TRACE_ID, message_data, opt_out_data, page_of


class TestPaginated:
    def test_reads_a_page_with_its_links_and_meta(self) -> None:
        page = Paginated.from_dict(page_of([message_data(), message_data()], "messages", 2, True), Message.from_dict)

        assert [message.id for message in page.data] == [MESSAGE_ID, MESSAGE_ID]
        assert page.links == PaginationLinks(
            first="https://rest.calisero.ro/api/v1/messages?page=1",
            last=None,
            prev="https://rest.calisero.ro/api/v1/messages?page=1",
            next="https://rest.calisero.ro/api/v1/messages?page=3",
        )
        assert page.meta == PaginationMeta(
            current_page=2, from_=51, path="https://rest.calisero.ro/api/v1/messages", per_page=50, to=52
        )
        assert page.has_next_page
        assert page.response_meta == ResponseMeta()

    def test_reads_an_empty_last_page(self) -> None:
        page = Paginated.from_dict(page_of([], "opt-outs", 3), OptOut.from_dict)

        assert page.data == ()
        assert (page.meta.from_, page.meta.to) == (None, None)
        assert not page.has_next_page

    def test_iterates_over_its_items(self) -> None:
        page = Paginated.from_dict(page_of([opt_out_data(), opt_out_data(reason=None)], "opt-outs"), OptOut.from_dict)

        assert len(page) == 2
        assert [opt_out.reason for opt_out in page] == ["Customer asked to stop receiving messages", None]

    @pytest.mark.parametrize(
        ("data", "message"),
        [
            ({**page_of([], "messages"), "data": None}, 'Invalid page: "data" must be an array, got null.'),
            ({**page_of([], "messages"), "links": []}, 'Invalid page: "links" must be an object, got an array.'),
            (
                {**page_of([], "messages"), "meta": {"current_page": 1}},
                'Invalid page.meta: "path" must be a string, got nothing.',
            ),
            (page_of([{"id": 42}], "messages"), 'Invalid page.data[0]: "id" must be a string, got a number.'),
        ],
    )
    def test_refuses_a_malformed_page_naming_the_field_at_fault(self, data: object, message: str) -> None:
        with pytest.raises(TypeError) as caught:
            Paginated.from_dict(data, Message.from_dict)

        assert str(caught.value) == message


class TestResponseMeta:
    def test_reads_the_headers_of_an_answer_in_any_case(self) -> None:
        response = HttpResponse(
            201,
            {
                "x-trace-id": TRACE_ID,
                "X-RateLimit-Limit": "240",
                "X-RATELIMIT-REMAINING": "239",
                "X-Daily-Limit": "1000",
                "x-daily-remaining": "872",
            },
        )

        assert ResponseMeta.from_response(response) == ResponseMeta(
            trace_id=TRACE_ID, rate_limit_limit=240, rate_limit_remaining=239, daily_limit=1000, daily_remaining=872
        )

    def test_ignores_values_that_are_not_counts(self) -> None:
        response = HttpResponse(
            200, {"X-Trace-Id": "  ", "X-RateLimit-Limit": "abc", "X-Daily-Limit": "-1", "X-Daily-Remaining": "1.5"}
        )

        assert ResponseMeta.from_response(response) == ResponseMeta()

    def test_is_empty_without_an_answer(self) -> None:
        assert ResponseMeta.from_response(None) == ResponseMeta()

    def test_an_api_response_has_an_empty_meta_by_default(self) -> None:
        assert ApiResponse("data").response_meta == ResponseMeta()
