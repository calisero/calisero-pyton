"""The internal helpers, on the inputs the API's answers rarely bring."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from calisero import BearerTokenAuthProvider
from calisero._internal import json as internal_json
from calisero._internal.fields import FieldReader, to_integer, to_number
from calisero._internal.json import MISSING, describe_value, dumps, loads


@pytest.mark.parametrize(
    ("value", "description"),
    [
        (MISSING, "nothing"),
        (None, "null"),
        (True, "a boolean"),
        (1, "a number"),
        (1.5, "a number"),
        ("text", "a string"),
        ([], "an array"),
        ((), "an array"),
        ({}, "an object"),
        (b"bytes", "a bytes"),
    ],
)
def test_describes_a_value_for_error_messages(value: object, description: str) -> None:
    assert describe_value(value) == description


def test_shows_a_missing_value_as_such() -> None:
    assert repr(MISSING) == "MISSING"


def test_names_an_object_where_another_type_was_expected() -> None:
    with pytest.raises(TypeError, match=r'^Invalid page: "data" must be an array, got an object\.$'):
        FieldReader.of({"data": {}}, "page").array("data")


@pytest.mark.parametrize(
    ("value", "integer"),
    [(3, 3), (3.0, 3), (-2, -2), (3.5, None), ("3", None), (True, None), (None, None), (2.0**53, None)],
)
def test_reads_integers_as_javascript_does(value: object, integer: int | None) -> None:
    assert to_integer(value) == integer


@pytest.mark.parametrize(
    ("value", "number"),
    [(1, 1.0), (0.5, 0.5), ("0.0378", 0.0378), ("-.5", -0.5), ("5.", 5.0), ("0x10", None), (float("inf"), None)],
)
def test_reads_numbers_and_decimal_strings(value: object, number: float | None) -> None:
    assert to_number(value) == number


def test_writes_json_as_javascript_does() -> None:
    assert dumps({"body": "Bună ziua!", "parts": 1}) == '{"body":"Bună ziua!","parts":1}'


@pytest.mark.parametrize("text", ["NaN", "Infinity", "-Infinity", '{"credit": NaN}'])
def test_refuses_the_constants_json_does_not_have(text: str) -> None:
    with pytest.raises(ValueError, match="is not valid JSON"):
        loads(text)


def test_turns_a_decoder_out_of_stack_into_a_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # How deep the decoder can go depends on the platform's stack: the overflow is simulated
    def overflow(text: str, **kwargs: object) -> object:
        raise RecursionError("maximum recursion depth exceeded")

    monkeypatch.setattr(internal_json, "json", SimpleNamespace(loads=overflow))

    with pytest.raises(ValueError, match=r"^The JSON nests too deeply\.$") as caught:
        loads("[[[")

    assert isinstance(caught.value.__cause__, RecursionError)


def test_hides_the_api_key_when_the_auth_provider_is_printed() -> None:
    assert repr(BearerTokenAuthProvider("secret-key")) == "BearerTokenAuthProvider(token='***')"
