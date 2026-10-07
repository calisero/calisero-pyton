"""Opt a phone number out: the API then refuses to send it messages.

CALISERO_API_KEY=... CALISERO_TEST_PHONE=+40742123456 python examples/optouts/create_optout.py
"""

from __future__ import annotations

import os

from calisero import ApiError, SmsClient, ValidationError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"
PHONE = os.environ.get("CALISERO_TEST_PHONE") or "+40742***350"


def main() -> None:
    print("=== Create OptOut ===\n")

    try:
        opt_out = (
            SmsClient.create(API_KEY)
            .opt_outs.create(phone=PHONE, reason="Customer requested to stop receiving marketing messages")
            .data
        )
    except ValidationError as error:
        # e.g. a number already opted out
        print(f"❌ Validation error: {error.message}")

        for field, messages in error.validation_errors.items():
            print(f"  - {field}: {', '.join(messages)}")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ Opt-out created successfully!")
    print(f"🆔 OptOut ID: {opt_out.id}")
    print(f"📱 Phone Number: {opt_out.phone}")
    print(f"📝 Reason: {opt_out.reason or 'Not specified'}")
    print(f"⏰ Created: {opt_out.created_at}")
    print(f"🔄 Updated: {opt_out.updated_at}")
    print("\n💡 This phone number will no longer receive SMS messages")


if __name__ == "__main__":
    main()
