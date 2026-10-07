from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from calisero._internal.fields import FieldReader
from calisero.models.response import ResponseMeta

T = TypeVar("T")

#: Reads a model out of a decoded JSON value, naming it `context` in errors.
ItemReader = Callable[[object, str], T]


@dataclass(frozen=True, slots=True, kw_only=True)
class PaginationLinks:
    """The URLs of the neighbouring pages; None when there is none."""

    first: str | None

    #: Always None: the API does not count the pages.
    last: str | None

    prev: str | None

    #: None on the last page.
    next: str | None

    @classmethod
    def from_dict(cls, data: object, context: str = "pagination links") -> PaginationLinks:
        read = FieldReader.of(data, context)

        return cls(
            first=read.optional_string("first"),
            last=read.optional_string("last"),
            prev=read.optional_string("prev"),
            next=read.optional_string("next"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class PaginationMeta:
    """Where the page stands in the whole list."""

    current_page: int

    #: The position of the page's first item in the whole list; None on an empty page. The API
    #: names it `from`, a Python keyword.
    from_: int | None

    path: str
    per_page: int

    #: The position of the page's last item in the whole list; None on an empty page.
    to: int | None

    @classmethod
    def from_dict(cls, data: object, context: str = "pagination meta") -> PaginationMeta:
        read = FieldReader.of(data, context)

        return cls(
            current_page=read.integer("current_page"),
            from_=read.optional_integer("from"),
            path=read.string("path"),
            per_page=read.integer("per_page"),
            to=read.optional_integer("to"),
        )


@dataclass(frozen=True)
class Paginated(Generic[T]):
    """A page of a list: its items, the links to the other pages and where it stands.

    Iterating over the page iterates over its items.
    """

    data: tuple[T, ...]
    links: PaginationLinks
    meta: PaginationMeta

    #: The answer's headers: trace id and request rate limit.
    response_meta: ResponseMeta = field(default_factory=ResponseMeta)

    @property
    def has_next_page(self) -> bool:
        """Whether a next page exists."""
        return self.links.next is not None

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    @classmethod
    def from_dict(
        cls,
        data: object,
        item: ItemReader[T],
        context: str = "page",
        response_meta: ResponseMeta | None = None,
    ) -> Paginated[T]:
        """Read a page as the API sends it, each item with `item` (e.g. `Message.from_dict`).

        Raises:
            TypeError: when a required field is missing or malformed
        """
        read = FieldReader.of(data, context)

        return cls(
            data=tuple(item(entry, f"{context}.data[{index}]") for index, entry in enumerate(read.array("data"))),
            links=PaginationLinks.from_dict(read.json_object("links"), f"{context}.links"),
            meta=PaginationMeta.from_dict(read.json_object("meta"), f"{context}.meta"),
            response_meta=response_meta if response_meta is not None else ResponseMeta(),
        )
