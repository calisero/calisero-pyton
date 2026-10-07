"""The bodies of the requests that create or change a resource, under the API's field names.

Optional fields left as None are not sent; False and 0 are.
"""

from __future__ import annotations

from datetime import datetime

from calisero._internal.schedule import format_schedule_at


def create_message_payload(
    *,
    recipient: str,
    body: str,
    visible_body: str | None = None,
    validity: int | None = None,
    schedule_at: datetime | str | None = None,
    callback_url: str | None = None,
    sender: str | None = None,
    shorten_urls: bool | None = None,
) -> dict[str, object]:
    """The body of `POST /messages`."""
    return _without_none(
        {
            "recipient": recipient,
            "body": body,
            "visible_body": visible_body,
            "validity": validity,
            "schedule_at": format_schedule_at(schedule_at) if schedule_at is not None else None,
            "callback_url": callback_url,
            "sender": sender,
            "shorten_urls": shorten_urls,
        }
    )


def opt_out_payload(*, phone: str, reason: str | None = None) -> dict[str, object]:
    """The body of `POST /opt-outs` and `PUT /opt-outs/{id}`."""
    return _without_none({"phone": phone, "reason": reason})


def create_verification_payload(
    *,
    phone: str,
    brand: str | None = None,
    template: str | None = None,
    expires_in: int | None = None,
) -> dict[str, object]:
    """The body of `POST /verifications`."""
    return _without_none({"phone": phone, "brand": brand, "template": template, "expires_in": expires_in})


def verification_check_payload(*, phone: str, code: str) -> dict[str, object]:
    """The body of `PUT /verifications/validate`."""
    return {"phone": phone, "code": code}


def _without_none(data: dict[str, object]) -> dict[str, object]:
    return {name: value for name, value in data.items() if value is not None}
