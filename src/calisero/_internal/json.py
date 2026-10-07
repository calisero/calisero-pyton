"""JSON helpers shared by the HTTP client, the models and the webhook payload reader."""

from __future__ import annotations

import json
from typing import Final, TypeGuard


class _Missing:
    """A key absent from a JSON object, which is not the same as one set to null."""

    def __repr__(self) -> str:
        return "MISSING"


MISSING: Final = _Missing()


def is_json_object(value: object) -> TypeGuard[dict[str, object]]:
    """Whether a decoded JSON value is an object (a dict), not an array nor a scalar."""
    return isinstance(value, dict)


def describe_value(value: object) -> str:
    """What a value is, for error messages: `null`, `an array`, `a string`..."""
    if value is MISSING:
        return "nothing"

    if value is None:
        return "null"

    # bool before int: True is an int in Python
    if isinstance(value, bool):
        return "a boolean"

    if isinstance(value, (int, float)):
        return "a number"

    if isinstance(value, str):
        return "a string"

    if isinstance(value, (list, tuple)):
        return "an array"

    if isinstance(value, dict):
        return "an object"

    return f"a {type(value).__name__}"


def loads(text: str | bytes) -> object:
    """Decode JSON as the API and JavaScript write it.

    NaN and Infinity, which Python's decoder accepts but JSON does not, are refused.

    Raises:
        ValueError: when the text is not JSON, or nests too deeply to decode
    """
    try:
        return json.loads(text, parse_constant=_refuse_constant)
    except RecursionError as error:
        raise ValueError("The JSON nests too deeply.") from error


def dumps(data: object) -> str:
    """Encode JSON as JavaScript's JSON.stringify(): compact, the text as UTF-8 characters, no NaN."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _refuse_constant(name: str) -> object:
    raise ValueError(f"{name} is not valid JSON.")
