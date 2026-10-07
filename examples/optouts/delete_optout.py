"""Delete an opt-out: the number can receive messages again.

CALISERO_API_KEY=... python examples/optouts/delete_optout.py <opt-out-id>
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, NotFoundError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    opt_out_id = sys.argv[1] if len(sys.argv) > 1 else "019999b5-5687-71cd-ae81-baf6eea9d86f"
    client = SmsClient.create(API_KEY)

    print("=== Delete OptOut ===\n")

    try:
        print("1️⃣ Checking current opt-out status...")
        opt_out = client.opt_outs.get(opt_out_id).data

        print("✅ Opt-out found:")
        print(f"   🆔 ID: {opt_out.id}")
        print(f"   📱 Phone: {opt_out.phone}")
        print(f"   📝 Reason: {opt_out.reason or 'Not specified'}\n")

        print("2️⃣ Removing opt-out (re-enabling SMS delivery)...")
        client.opt_outs.delete(opt_out_id)

        print("✅ Opt-out deleted successfully!")
        print(f"💡 {opt_out.phone} can now receive SMS messages again")

        print("\n3️⃣ Verifying deletion...")

        try:
            client.opt_outs.get(opt_out_id)
            print("⚠️ Opt-out still exists")
        except NotFoundError:
            print("✅ Confirmed: Opt-out has been removed")
    except NotFoundError:
        print(f"❌ No opt-out found with ID: {opt_out_id}")
        print("💡 The phone number may already be able to receive messages")
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")


if __name__ == "__main__":
    main()
