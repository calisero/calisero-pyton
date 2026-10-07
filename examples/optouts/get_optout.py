"""Retrieve an opt-out by its id.

CALISERO_API_KEY=... python examples/optouts/get_optout.py <opt-out-id>
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, NotFoundError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    opt_out_id = sys.argv[1] if len(sys.argv) > 1 else "019999b5-5687-71cd-ae81-baf6eea9d86f"

    print("=== Get OptOut ===\n")

    try:
        opt_out = SmsClient.create(API_KEY).opt_outs.get(opt_out_id).data
    except NotFoundError:
        print(f"❌ No opt-out found with ID: {opt_out_id}")
        print("💡 Make sure the opt-out ID exists")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ Opt-out found!")
    print(f"🆔 OptOut ID: {opt_out.id}")
    print(f"📱 Phone Number: {opt_out.phone}")
    print(f"📝 Reason: {opt_out.reason or 'Not specified'}")
    print(f"⏰ Created: {opt_out.created_at}")
    print(f"🔄 Last Updated: {opt_out.updated_at}")
    print("\n🚫 This phone number is currently opted out from receiving SMS messages")


if __name__ == "__main__":
    main()
