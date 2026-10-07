"""What the services share: reading the answers, the page query, the ids in the paths."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar
from urllib.parse import quote

from calisero._internal.fields import FieldError, FieldReader
from calisero._internal.json import is_json_object
from calisero.errors import ApiError
from calisero.http._headers import read_header_string
from calisero.http.client import HttpResult
from calisero.models.pagination import ItemReader, Paginated
from calisero.models.response import ApiResponse, ResponseMeta

T = TypeVar("T")


def read_single(result: HttpResult, item: ItemReader[T], context: str) -> ApiResponse[T]:
    """An answer holding one resource as `data`."""

    def read(body: object) -> ApiResponse[T]:
        data = FieldReader.of(body, f"{context} answer").json_object("data")

        return ApiResponse(item(data, context), ResponseMeta.from_response(result.response))

    return _parse(result, read)


def read_page(result: HttpResult, item: ItemReader[T]) -> Paginated[T]:
    """An answer holding a page of resources."""

    def read(body: object) -> Paginated[T]:
        return Paginated.from_dict(body, item, "page", ResponseMeta.from_response(result.response))

    return _parse(result, read)


def page_query(page: int | None) -> dict[str, int]:
    """The query of a list call: the page, sent only from the second one on.

    Raises:
        TypeError: when the page is not an integer
        ValueError: when it is lower than 1
    """
    if page is None:
        return {}

    message = f"The page must be a positive integer, got {page!r}."

    if isinstance(page, bool) or not isinstance(page, int):
        raise TypeError(message)

    if page < 1:
        raise ValueError(message)

    return {"page": page} if page > 1 else {}


def path_id(value: str, name: str) -> str:
    """An id in a request path, encoded.

    Refused when empty, which would change the request's meaning (`DELETE /messages/`
    instead of `DELETE /messages/{id}`).

    Raises:
        TypeError: when it is not a string
        ValueError: when it is empty
    """
    message = f"The {name} must be a non-empty string."

    if not isinstance(value, str):
        raise TypeError(message)

    if value.strip() == "":
        raise ValueError(message)

    # As JavaScript's encodeURIComponent()
    return quote(value, safe="!~*'()")


def _parse(result: HttpResult, read: Callable[[object], T]) -> T:
    """Read the models out of an answer.

    An answer that is not what the API documents becomes an ApiError carrying its
    status, trace id and body.
    """
    try:
        return read(result.body)
    except FieldError as error:
        raise ApiError(
            f"Unexpected API response: {error}",
            status_code=result.response.status,
            trace_id=read_header_string(result.response, "X-Trace-Id"),
            error_details=result.body if is_json_object(result.body) else {},
        ) from error
