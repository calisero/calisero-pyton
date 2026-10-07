from __future__ import annotations

from dataclasses import dataclass

from calisero._internal.fields import FieldReader
from calisero.models.shortened_link import ShortenedLink


@dataclass(frozen=True, slots=True, kw_only=True)
class Message:
    """An SMS message."""

    id: str

    #: The recipient's phone number.
    recipient: str

    body: str

    #: How many SMS parts the body takes.
    parts: int

    created_at: str
    scheduled_at: str | None
    sent_at: str | None
    delivered_at: str | None
    callback_url: str | None

    #: The message's status: compare it with the `MessageStatus` constants.
    status: str

    #: The sender ID; None for the default sender.
    sender: str | None

    #: The links of the body Calisero shortened (requested with `shorten_urls`), with their click
    #: statistics; empty when none were.
    shortened_urls: tuple[ShortenedLink, ...] = ()

    @classmethod
    def from_dict(cls, data: object, context: str = "message") -> Message:
        """Read a message as the API sends it.

        Raises:
            TypeError: when a required field is missing or malformed
        """
        read = FieldReader.of(data, context)

        return cls(
            id=read.string("id"),
            recipient=read.string("recipient"),
            body=read.string("body"),
            parts=read.integer("parts"),
            created_at=read.string("created_at"),
            scheduled_at=read.optional_string("scheduled_at"),
            sent_at=read.optional_string("sent_at"),
            delivered_at=read.optional_string("delivered_at"),
            callback_url=read.optional_string("callback_url"),
            status=read.string("status"),
            sender=read.optional_string("sender"),
            shortened_urls=tuple(
                ShortenedLink.from_dict(link, f"{context}.shortened_urls[{index}]")
                for index, link in enumerate(read.optional_array("shortened_urls"))
            ),
        )
