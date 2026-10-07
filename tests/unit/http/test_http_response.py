from __future__ import annotations

from email.message import Message

from calisero import HttpResponse


def test_matches_header_names_case_insensitively_as_http_defines_them() -> None:
    response = HttpResponse(200, {"X-Trace-Id": "trace", "content-type": "application/json"})

    assert response.get_header("x-trace-id") == ["trace"]
    assert response.get_header("X-TRACE-ID") == ["trace"]
    assert response.get_header("Content-Type") == ["application/json"]
    assert response.has_header("CONTENT-TYPE")
    assert not response.has_header("X-Daily-Limit")


def test_gives_an_empty_list_and_line_for_a_header_it_did_not_carry() -> None:
    response = HttpResponse(200)

    assert response.get_header("X-Trace-Id") == []
    assert response.get_header_line("X-Trace-Id") == ""
    assert response.headers == {}


def test_keeps_every_value_of_a_repeated_header() -> None:
    response = HttpResponse(200, [("Set-Cookie", "a=1"), ("set-cookie", "b=2"), ("Vary", "Accept")])

    assert response.get_header("Set-Cookie") == ["a=1", "b=2"]
    assert response.get_header_line("Set-Cookie") == "a=1, b=2"
    assert response.headers == {"set-cookie": ["a=1", "b=2"], "vary": ["Accept"]}


def test_takes_lists_of_values_in_a_mapping_and_skips_none() -> None:
    headers: dict[str, object] = {"Vary": ["Accept", "Origin"], "X-Trace-Id": "trace", "X-Missing": None}
    response = HttpResponse(200, headers)  # type: ignore[arg-type]

    assert response.headers == {"vary": ["Accept", "Origin"], "x-trace-id": ["trace"]}


def test_takes_the_headers_of_an_http_library() -> None:
    # urllib's headers are an email Message, which gives every value of a repeated header
    headers = Message()
    headers["X-RateLimit-Limit"] = "240"
    headers["Set-Cookie"] = "a=1"
    headers["Set-Cookie"] = "b=2"

    response = HttpResponse(200, headers)  # type: ignore[arg-type]

    assert response.get_header("x-ratelimit-limit") == ["240"]
    assert response.get_header("set-cookie") == ["a=1", "b=2"]


def test_returns_copies_of_the_headers() -> None:
    response = HttpResponse(200, {"X-Trace-Id": "trace"})

    response.get_header("X-Trace-Id").append("changed")
    response.headers["x-trace-id"].append("changed")

    assert response.get_header("X-Trace-Id") == ["trace"]


def test_decodes_a_body_given_as_bytes_as_utf8() -> None:
    assert HttpResponse(200, {}, "Bună ziua!".encode()).body == "Bună ziua!"
    assert HttpResponse(200, {}, b"\xff\xfe broken").body == "�� broken"


def test_shows_its_status_headers_and_body() -> None:
    response = HttpResponse(201, {"X-Trace-Id": "trace"}, "{}")

    assert repr(response) == "HttpResponse(status=201, headers={'x-trace-id': ['trace']}, body='{}')"
