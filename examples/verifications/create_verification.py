"""Start a verification: Calisero generates a 6-character code and sends it by SMS.

CALISERO_API_KEY=... CALISERO_TEST_PHONE=+40742123456 python examples/verifications/create_verification.py
"""

from __future__ import annotations

import os

from calisero import ApiError, DailyLimitExceededError, SmsClient, ValidationError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"
PHONE = os.environ.get("CALISERO_TEST_PHONE") or "+40742***350"


def main() -> None:
    print("=== Create Verification (OTP) ===\n")

    try:
        response = SmsClient.create(API_KEY).verifications.create(
            phone=PHONE,
            # The brand named in the default message; or pass a `template` holding {code}
            brand="Calisero",
            expires_in=5,  # minutes, 1 to 10
        )
    except DailyLimitExceededError as error:
        print(f"❌ Daily sending limit reached, no code was sent: {error.message}")
        print(f"⏰ Sending resumes at: {error.resets_at or 'midnight, Romania time'}")

        return
    except ValidationError as error:
        print(f"❌ Validation error: {error.message}")

        for field, messages in error.validation_errors.items():
            print(f"  - {field}: {', '.join(messages)}")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    verification = response.data

    print("✅ Verification created successfully!")
    print(f"🆔 ID: {verification.id}")
    print(f"📱 Phone: {verification.phone}")
    print(f"🏷️ Brand: {verification.brand or 'N/A'}")
    print(f"📊 Status: {verification.status}")
    print(f"⏰ Expires at: {verification.expires_at}")
    print(f"🧪 Attempts: {verification.attempts}")

    # The code's SMS counts towards the account's daily sending limit
    daily_remaining = response.response_meta.daily_remaining

    if daily_remaining is not None:
        print(f"📊 Daily limit: {daily_remaining} messages left today")


if __name__ == "__main__":
    main()
