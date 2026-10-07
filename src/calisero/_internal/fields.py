"""Reads the fields of decoded JSON objects, naming the field at fault in errors."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Final

from calisero._internal.json import MISSING, describe_value, is_json_object

#: Builds the exception raised for a missing or malformed field.
ErrorFactory = Callable[[str], Exception]

#: The largest integer a JSON number holds exactly (JavaScript's Number.MAX_SAFE_INTEGER).
MAX_SAFE_INTEGER: Final = 2**53 - 1

# A decimal number written as text: amounts may come as strings ("0.0378")
_DECIMAL: Final = re.compile(r"\s*[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\s*")


class FieldError(TypeError):
    """A field of a decoded JSON object is missing or malformed."""


def _field_error(message: str) -> Exception:
    return FieldError(message)


class FieldReader:
    """Reads the fields of a decoded JSON object.

    A required field that is missing or of the wrong type raises an error naming it;
    an optional one reads as None.
    """

    __slots__ = ("_context", "_data", "_error")

    def __init__(self, data: dict[str, object], context: str, error: ErrorFactory) -> None:
        self._data = data
        self._context = context
        self._error = error

    @classmethod
    def of(cls, data: object, context: str, error: ErrorFactory = _field_error) -> FieldReader:
        """A reader of `data`, which must be an object; `context` names it in errors."""
        if not is_json_object(data):
            raise error(f"Invalid {context}: expected an object, got {describe_value(data)}.")

        return cls(data, context, error)

    def string(self, key: str) -> str:
        value = self._get(key)

        if not isinstance(value, str):
            raise self._invalid(key, "a string", value)

        return value

    def non_empty_string(self, key: str) -> str:
        value = self._get(key)

        if not isinstance(value, str) or value == "":
            raise self._invalid(key, "a non-empty string", value)

        return value

    def optional_string(self, key: str) -> str | None:
        value = self._get(key)

        return value if isinstance(value, str) else None

    def integer(self, key: str) -> int:
        value = self._get(key)
        integer = to_integer(value)

        if integer is None:
            raise self._invalid(key, "an integer", value)

        return integer

    def optional_integer(self, key: str) -> int | None:
        return to_integer(self._get(key))

    def number(self, key: str) -> float:
        """A finite number, or a string holding one (amounts may come as strings)."""
        value = self._get(key)
        number = to_number(value)

        if number is None:
            raise self._invalid(key, "a number", value)

        return number

    def optional_number(self, key: str) -> float | None:
        return to_number(self._get(key))

    def boolean(self, key: str) -> bool:
        value = self._get(key)

        if not isinstance(value, bool):
            raise self._invalid(key, "a boolean", value)

        return value

    def json_object(self, key: str) -> dict[str, object]:
        value = self._get(key)

        if not is_json_object(value):
            raise self._invalid(key, "an object", value)

        return value

    def array(self, key: str) -> list[object]:
        value = self._get(key)

        if not isinstance(value, list):
            raise self._invalid(key, "an array", value)

        return value

    def optional_array(self, key: str) -> list[object]:
        """The array under `key`, or an empty list when it is absent or not one."""
        value = self._get(key)

        return value if isinstance(value, list) else []

    def _get(self, key: str) -> object:
        return self._data.get(key, MISSING)

    def _invalid(self, key: str, expected: str, value: object) -> Exception:
        return self._error(f'Invalid {self._context}: "{key}" must be {expected}, got {describe_value(value)}.')


def to_integer(value: object) -> int | None:
    """An integer, as JavaScript reads one from JSON: 3 and 3.0 are, 3.5, "3" and True are not."""
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float) and value.is_integer() and abs(value) <= MAX_SAFE_INTEGER:
        return int(value)

    return None


def to_number(value: object) -> float | None:
    """A finite number, or a string holding one in decimal notation; None for anything else."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None

    # float() alone would also read "inf", "nan" and "1_000"
    if isinstance(value, str) and not _DECIMAL.fullmatch(value):
        return None

    number = float(value)

    return number if math.isfinite(number) else None
