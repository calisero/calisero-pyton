from __future__ import annotations

from dataclasses import dataclass

from calisero._internal.fields import FieldReader


@dataclass(frozen=True, slots=True, kw_only=True)
class ShortenedLink:
    """A link of a message body shortened by Calisero, with its click statistics."""

    id: str

    #: The URL as it was written in the message body.
    original_link: str

    #: The short URL that replaced it in the SMS sent.
    shortened_link: str

    #: How many times the short URL was opened.
    click_count: int

    #: When the short URL was last opened; None if it never was.
    last_click: str | None

    created_at: str

    @classmethod
    def from_dict(cls, data: object, context: str = "shortened link") -> ShortenedLink:
        """Read a shortened link as the API sends it.

        Raises:
            TypeError: when a required field is missing or malformed
        """
        read = FieldReader.of(data, context)

        return cls(
            id=read.string("id"),
            original_link=read.string("original_link"),
            shortened_link=read.string("shortened_link"),
            click_count=read.optional_integer("click_count") or 0,
            last_click=read.optional_string("last_click"),
            created_at=read.string("created_at"),
        )
