"""Reads the values the API reports in its answers' headers."""

from __future__ import annotations

import re
from typing import Final

from calisero._internal.fields import MAX_SAFE_INTEGER
from calisero.http.response import HttpResponse

# ASCII digits only: \d would also match the digits of other scripts
_DIGITS: Final = re.compile(r"[0-9]+")


def read_header_string(response: HttpResponse, name: str) -> str | None:
    """The header's first value, trimmed; None when the header is absent or empty."""
    values = response.get_header(name)
    value = values[0].strip() if values else ""

    return value if value != "" else None


def read_header_int(response: HttpResponse, name: str) -> int | None:
    """The header's value as a non-negative integer; None when it is absent or not one."""
    value = read_header_string(response, name)

    if value is None or not _DIGITS.fullmatch(value):
        return None

    number = int(value)

    return number if number <= MAX_SAFE_INTEGER else None
