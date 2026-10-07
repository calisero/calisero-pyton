"""Retrieve a verification by its id.

CALISERO_API_KEY=... python examples/verifications/get_verification.py <verification-id>
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, NotFoundError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    verification_id = sys.argv[1] if len(sys.argv) > 1 else "019a62f1-66b7-7387-a64f-2742c12a2860"

    print("=== Get Verification ===\n")

    try:
        verification = SmsClient.create(API_KEY).verifications.get(verification_id).data
    except NotFoundError as error:
        print(f"❌ Verification not found: {error.message}")
        print(f"💡 Please check if the verification ID '{verification_id}' is correct")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ Verification retrieved successfully!")
    print(f"🆔 ID: {verification.id}")
    print(f"📱 Phone: {verification.phone}")
    print(f"📊 Status: {verification.status}")
    print(f"✅ Verified at: {verification.verified_at or 'Not verified yet'}")
    print(f"⏰ Expires at: {verification.expires_at}")
    print(f"🧪 Attempts: {verification.attempts}")
    print(f"⌛ Expired: {'Yes' if verification.expired else 'No'}")


if __name__ == "__main__":
    main()
