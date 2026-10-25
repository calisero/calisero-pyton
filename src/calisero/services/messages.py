from __future__ import annotations

from datetime import datetime
from typing import TypeAlias

from calisero._payloads import create_message_payload
from calisero.http.client import HttpClient
from calisero.models.message import Message
from calisero.models.pagination import Paginated
from calisero.models.response import ApiResponse
from calisero.services._support import page_query, path_id, read_page, read_single

CreateMessageResponse: TypeAlias = ApiResponse[Message]
GetMessageResponse: TypeAlias = ApiResponse[Message]
PaginatedMessages: TypeAlias = Paginated[Message]


class MessageService:
    """Sends and manages SMS messages.

    Every call takes an optional `timeout`: seconds to wait for its answer, instead of
    the client's.
    """

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def create(
        self,
        *,
        recipient: str,
        body: str,
        visible_body: str | None = None,
        validity: int | None = None,
        schedule_at: datetime | str | None = None,
        callback_url: str | None = None,
        sender: str | None = None,
        shorten_urls: bool | None = None,
        timeout: float | None = None,
    ) -> CreateMessageResponse:
        """Send a message, now or at `schedule_at`.

        Its `response_meta` holds what is left of the account's daily sending limit
        after this message.

        Args:
            recipient: the recipient's mobile number in international E.164 format, e.g. +40742123456
            body: the text sent, at most 1600 characters
            visible_body: what the API shows instead of `body` in its answers, its lists and the
                dashboard, e.g. the text with a code masked: "Your code is ******"
            validity: the message's validity period, in hours
            schedule_at: when to send it: a timezone-aware datetime, converted to Romania time, or a
                "YYYY-MM-DD HH:MM:SS" string in Romania time. Sent at once when omitted or already
                past today; from today to 5 years ahead
            callback_url: the URL Calisero posts the message's delivery status updates to: a public
                http or https address (private, loopback and link-local ones are refused)
            sender: one of the account's approved sender IDs, written exactly as approved (the match
                is case-sensitive); the default sender when omitted
            shorten_urls: replace the http:// and https:// links of the body with short ones, whose
                clicks are counted
            timeout: seconds to wait for the answer, instead of the client's

        Raises:
            DailyLimitExceededError: once the account's daily sending limit is reached
            ValidationError: when the request is refused, e.g. an invalid or opted-out recipient
        """
        payload = create_message_payload(
            recipient=recipient,
            body=body,
            visible_body=visible_body,
            validity=validity,
            schedule_at=schedule_at,
            callback_url=callback_url,
            sender=sender,
            shorten_urls=shorten_urls,
        )
        result = self._http_client.post("/messages", payload, timeout=timeout)

        return read_single(result, Message.from_dict, "message")

    def get(self, message_id: str, *, timeout: float | None = None) -> GetMessageResponse:
        """Retrieve a message by its id.

        Raises:
            NotFoundError: when there is no such message
        """
        result = self._http_client.get(f"/messages/{path_id(message_id, 'message id')}", timeout=timeout)

        return read_single(result, Message.from_dict, "message")

    def list(self, *, page: int | None = None, timeout: float | None = None) -> PaginatedMessages:
        """List the messages, newest first, 50 a page.

        Args:
            page: the page to read, from 1
            timeout: seconds to wait for the answer, instead of the client's
        """
        result = self._http_client.get("/messages", page_query(page), timeout=timeout)

        return read_page(result, Message.from_dict)

    def delete(self, message_id: str, *, timeout: float | None = None) -> None:
        """Cancel a scheduled message.

        Raises:
            ForbiddenError: when the message is already queued, sent or delivered
        """
        self._http_client.delete(f"/messages/{path_id(message_id, 'message id')}", timeout=timeout)
