"""A request to the API, as the client hands it to the transport."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]


@dataclass(frozen=True, slots=True, repr=False)
class HttpRequest:
    """A request to the API, as handed to the `Transport`."""

    method: HttpMethod

    #: The full URL, query string included.
    url: str

    headers: Mapping[str, str]

    #: The JSON body; None when the request has none.
    body: str | None = None

    #: Seconds to wait for the answer to this request; None for the transport's own timeout.
    timeout: float | None = None

    def __repr__(self) -> str:
        # The API key never shows up in a log or a traceback
        headers = {
            name: "Bearer ***" if name.lower() == "authorization" else value for name, value in self.headers.items()
        }

        return (
            f"HttpRequest(method={self.method!r}, url={self.url!r}, headers={headers!r}, "
            f"body={self.body!r}, timeout={self.timeout!r})"
        )
