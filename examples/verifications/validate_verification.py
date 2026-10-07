"""Check the code a user received against the latest verification of their phone.

CALISERO_API_KEY=... CALISERO_TEST_PHONE=+40742123456 python examples/verifications/validate_verification.py <code>
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, NotFoundError, SmsClient, ValidationError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"
PHONE = os.environ.get("CALISERO_TEST_PHONE") or "+40742***350"


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "ABC123"  # the 6-character code, in any case

    print("=== Validate Verification (OTP) ===\n")

    try:
        verification = SmsClient.create(API_KEY).verifications.validate(phone=PHONE, code=code).data
    except ValidationError as error:
        # A wrong code, an expired one, or too many attempts (5)
        print(f"❌ Validation failed: {error.message}")

        for field, messages in error.validation_errors.items():
            print(f"  - {field}: {', '.join(messages)}")

        return
    except NotFoundError:
        print(f"❌ No verification was started for {PHONE}")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ Verification validated successfully!")
    print(f"📱 Phone: {verification.phone}")
    print(f"📊 Status: {verification.status}")
    print(f"✅ Verified at: {verification.verified_at or 'Just verified / already verified'}")
    print(f"🧪 Attempts used: {verification.attempts}")


if __name__ == "__main__":
    main()
