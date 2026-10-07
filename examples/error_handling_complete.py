"""Every error the library raises, and how to handle each.

CALISERO_API_KEY=... python examples/error_handling_complete.py
"""

from __future__ import annotations

import os
import time

from calisero import (
    ApiError,
    DailyLimitExceededError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    ServerError,
    SmsClient,
    TransportError,
    UnauthorizedError,
    ValidationError,
)

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"
TRACE_ID = "9b80eef1-49d4-4502-85a8-febb68cc11a7"


def handle_sms_api_error(error: Exception) -> None:
    """Describe an error and what to do about it.

    The most specific classes come first: DailyLimitExceededError extends
    RateLimitedError, and every class extends ApiError.
    """
    if not isinstance(error, ApiError):
        print(f"   🔧 Not an API error: {error}")

        return

    print(f"   📝 Type: {type(error).__name__}")
    print(f"   💬 Message: {error.message}")
    print(f"   🔢 HTTP Status: {error.status_code or 'N/A'}")
    print(f"   🆔 Trace ID: {error.trace_id or 'N/A'}")

    match error:
        case UnauthorizedError():
            print("   🔧 Action: Check the API key")
        case ValidationError():
            print("   🔧 Action: Fix the request data")

            for field, messages in error.validation_errors.items():
                print(f"     - {field}: {', '.join(messages)}")
        case NotFoundError():
            print("   🔧 Action: Verify the resource exists and its ID is correct")
        case ForbiddenError():
            print("   🔧 Action: Check the permissions, or whether the operation is still possible")
        case DailyLimitExceededError():
            print("   🔧 Action: Nothing was sent or billed: stop sending until the limit resets,")
            print("      or ask Calisero to raise it")
            print(f"   📊 Daily limit: {error.daily_limit} messages, {error.daily_remaining} left today")
            print(f"   ⏰ Resets at: {error.resets_at or 'midnight, Romania time'}")
        case RateLimitedError():
            print(f"   🔧 Action: Wait {error.retry_after or 1} seconds, then retry")
            print(f"   📊 Requests left this minute: {error.rate_limit_remaining} of {error.rate_limit_limit}")
        case ServerError():
            print("   🔧 Action: Contact support with the trace ID if it persists")
            print("   ⚠️ Do not resend a message blindly: it may have been sent")
        case TransportError():
            print(f"   🔧 Action: Check the network ({error.__cause__ or 'no answer'})")
            print("   ⚠️ Do not resend a message blindly: it may have been sent")
        case _:
            print("   🔧 Action: See the API documentation for this status")


def main() -> None:
    print("=== Comprehensive Error Handling Examples ===\n")

    print("1️⃣ Authentication error (a real request with an invalid key)...")

    try:
        SmsClient.create("invalid-api-key").messages.create(recipient="+40742***350", body="Test message")
    except ApiError as error:
        handle_sms_api_error(error)

    print("\n2️⃣ Validation error (a real request with an invalid recipient)...")

    try:
        SmsClient.create(API_KEY).messages.create(recipient="invalid-phone", body="")
    except ApiError as error:
        handle_sms_api_error(error)

    print("\n3️⃣ Not found error (a real request for a message that does not exist)...")

    try:
        SmsClient.create(API_KEY).messages.get("00000000-0000-0000-0000-000000000000")
    except ApiError as error:
        handle_sms_api_error(error)

    print("\n4️⃣ Request rate limit (simulated)...")
    handle_sms_api_error(
        RateLimitedError(
            "Too Many Attempts.",
            status_code=429,
            trace_id=TRACE_ID,
            retry_after=17,
            rate_limit_limit=240,
            rate_limit_remaining=0,
            rate_limit_reset=int(time.time()) + 17,
        )
    )

    print("\n5️⃣ Daily sending limit (simulated)...")
    handle_sms_api_error(
        DailyLimitExceededError(
            "This account can send at most 1,000 messages a day. The limit resets at midnight, Romania time "
            "(2026-10-01T00:00:00+03:00). Contact us to raise it.",
            status_code=429,
            trace_id=TRACE_ID,
            error_details={"code": DailyLimitExceededError.ERROR_CODE},
            retry_after=21600,
            daily_limit=1000,
            daily_remaining=0,
            resets_at="2026-10-01T00:00:00+03:00",
        )
    )

    print("\n6️⃣ Server error (simulated)...")
    handle_sms_api_error(ServerError("Server Error", status_code=500, trace_id=TRACE_ID))

    print("\n7️⃣ Transport error (a real request to a host that does not answer)...")

    try:
        SmsClient.create(API_KEY, base_url="http://127.0.0.1:9/api/v1", timeout=2).messages.list()
    except ApiError as error:
        handle_sms_api_error(error)

    print("\n✨ Error handling examples completed!")
    print("\n💡 Best Practices:")
    print("  1. Catch the specific error classes first, then ApiError")
    print("  2. Log trace IDs for support (Developers → Debug in the dashboard)")
    print("  3. Wait Retry-After seconds on a RateLimitedError")
    print("  4. Stop sending on a DailyLimitExceededError until it resets")
    print("  5. Never retry a create after a timeout or a 5xx without checking: it may have been sent")


if __name__ == "__main__":
    main()
