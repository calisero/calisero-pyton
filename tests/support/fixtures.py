"""API payloads as the Calisero API sends them (field names, types and formats), shared by the tests."""

from __future__ import annotations

from typing import Final

TRACE_ID: Final = "9b80eef1-49d4-4502-85a8-febb68cc11a7"
MESSAGE_ID: Final = "9e2574e8-3615-4090-9b5a-0fc812079da8"
OPT_OUT_ID: Final = "019999b5-5687-71cd-ae81-baf6eea9d86f"
ACCOUNT_ID: Final = "9d0e0bd3-c805-4dd0-bafb-07c5ded0a8e1"
VERIFICATION_ID: Final = "019a62f1-66b7-7387-a64f-2742c12a2860"
PHONE: Final = "+40742***350"


def shortened_link_data(**overrides: object) -> dict[str, object]:
    return {
        "id": "019adfbb-40a1-71ee-bcb5-8d551b8cfdae",
        "original_link": "https://yourstore.com/orders/12345/tracking",
        "shortened_link": "https://calisero.ro/s/ghJKPV",
        "click_count": 3,
        "last_click": "2025-12-02T16:01:12.000000Z",
        "created_at": "2025-12-02T15:43:02.000000Z",
        **overrides,
    }


def message_data(**overrides: object) -> dict[str, object]:
    return {
        "id": MESSAGE_ID,
        "recipient": PHONE,
        "body": "Hello from Calisero!",
        "parts": 1,
        "created_at": "2025-02-06T10:18:43.000000Z",
        "scheduled_at": "2025-02-06T10:18:43.000000Z",
        "sent_at": None,
        "delivered_at": None,
        "callback_url": "https://yourapp.com/webhooks/calisero",
        "status": "scheduled",
        "sender": "CALISERO",
        "shortened_urls": [],
        **overrides,
    }


def opt_out_data(**overrides: object) -> dict[str, object]:
    return {
        "id": OPT_OUT_ID,
        "phone": PHONE,
        "reason": "Customer asked to stop receiving messages",
        "created_at": "2025-09-19T12:01:15.000000Z",
        "updated_at": "2025-09-19T12:01:15.000000Z",
        **overrides,
    }


def account_data(**overrides: object) -> dict[str, object]:
    return {
        "id": ACCOUNT_ID,
        "code": "ABC1234",
        "name": "My Company",
        "description": "Company description",
        "fiscal_code": "RO12345678",
        "registry_number": "J40/123456/2023",
        "iban": "RO49AAAA1B31007593840000",
        "city": "Bucharest",
        "state": "Bucharest",
        "country": "RO",
        "address": "Main Street 123",
        "postal_code": 123456,
        "email": "contact@company.com",
        "phone": "+40721***456",
        "contact_person": "John Doe",
        "credit": 100.5,
        "status": "active",
        "sandbox": False,
        "daily_limit": 1000,
        "daily_remaining": 873,
        "sent_today": 127,
        "created_at": "2024-09-20T12:48:55.000000Z",
        **overrides,
    }


def verification_data(**overrides: object) -> dict[str, object]:
    return {
        "id": VERIFICATION_ID,
        "phone": PHONE,
        "brand": "Calisero",
        "status": "unverified",
        "template": None,
        "created_at": "2025-11-08T10:09:38.000000Z",
        "expires_at": "2025-11-08T10:12:38.000000Z",
        "verified_at": None,
        "attempts": 0,
        "expired": False,
        **overrides,
    }


def webhook_payload(**overrides: object) -> dict[str, object]:
    return {
        "price": 0.0378,
        "sender": "CALISERO",
        "sentAt": "2025-09-19T12:01:15.000000Z",
        "status": "delivered",
        "messageId": "019961db-14a7-7348-963f-5a7a789a969f",
        "recipient": PHONE,
        "scheduleAt": "2025-09-19T12:02:51.000000Z",
        "deliveredAt": "2025-09-19T12:02:53.000000Z",
        "remainingBalance": 999.392,
        "dailyLimit": 1000,
        "dailyRemaining": 588,
        "sentToday": 412,
        **overrides,
    }


def without(data: dict[str, object], *keys: str) -> dict[str, object]:
    """The payload without some of its fields."""
    return {key: value for key, value in data.items() if key not in keys}


def page_of(items: list[object], resource: str, page: int = 1, has_next: bool = False) -> dict[str, object]:
    """A page of a list as the API sends it (simple pagination: no total, no last page)."""
    path = f"https://rest.calisero.ro/api/v1/{resource}"
    first = (page - 1) * 50 + 1 if items else None

    return {
        "data": items,
        "links": {
            "first": f"{path}?page=1",
            "last": None,
            "prev": f"{path}?page={page - 1}" if page > 1 else None,
            "next": f"{path}?page={page + 1}" if has_next else None,
        },
        "meta": {
            "current_page": page,
            "current_page_url": f"{path}?page={page}",
            "from": first,
            "path": path,
            "per_page": 50,
            "to": first + len(items) - 1 if first is not None else None,
        },
    }


DAILY_LIMIT_BODY: Final[dict[str, object]] = {
    "message": (
        "This account can send at most 1,000 messages a day. The limit resets at midnight, Romania time "
        "(2026-10-01T00:00:00+03:00). Contact us to raise it."
    ),
    "code": "daily_limit_exceeded",
    "daily_limit": 1000,
    "daily_remaining": 0,
    "resets_at": "2026-10-01T00:00:00+03:00",
    "trace_id": TRACE_ID,
}
