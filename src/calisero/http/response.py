"""The raw answer of the API: status, headers and body."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TypeAlias, cast

#: The headers an `HttpResponse` is built from: a mapping whose values are strings or lists of
#: strings, any iterable of (name, value) pairs, or an object whose `items()` method gives those
#: pairs (e.g. the headers of urllib, requests or httpx).
ResponseHeaders: TypeAlias = Mapping[str, str | Sequence[str]] | Iterable[tuple[str, str]]


class HttpResponse:
    """The raw answer of the API: status, headers and body."""

    __slots__ = ("_headers", "body", "status")

    def __init__(self, status: int, headers: ResponseHeaders | None = None, body: str | bytes = "") -> None:
        """Build an answer; a body given as bytes is decoded as UTF-8, the encoding of JSON."""
        #: The HTTP status code.
        self.status: int = status

        #: The body as received; empty when there was none.
        self.body: str = body if isinstance(body, str) else bytes(body).decode("utf-8", errors="replace")

        self._headers: dict[str, list[str]] = {}

        for name, value in _entries(headers):
            if value is None:
                continue

            values = [value] if isinstance(value, str) else list(value)
            self._headers.setdefault(name.lower(), []).extend(values)

    @property
    def headers(self) -> dict[str, list[str]]:
        """All headers, their names in lowercase."""
        return {name: list(values) for name, values in self._headers.items()}

    def get_header(self, name: str) -> list[str]:
        """The values of a header, its name matched case-insensitively as HTTP defines them.

        Empty when the answer did not carry it.
        """
        return list(self._headers.get(name.lower(), []))

    def get_header_line(self, name: str) -> str:
        """The values of a header joined with a comma; empty when the answer did not carry it."""
        return ", ".join(self.get_header(name))

    def has_header(self, name: str) -> bool:
        return name.lower() in self._headers

    def __repr__(self) -> str:
        return f"HttpResponse(status={self.status!r}, headers={self._headers!r}, body={self.body!r})"


def _entries(headers: ResponseHeaders | None) -> Iterable[tuple[str, Any]]:
    """The (name, value) pairs of the headers, however they are given."""
    if headers is None:
        return ()

    items = getattr(headers, "items", None)

    # A mapping, or the headers of an HTTP library (urllib's keep every value of a repeated header)
    if callable(items):
        pairs: Iterable[tuple[str, Any]] = items()

        return pairs

    return cast("Iterable[tuple[str, Any]]", headers)
