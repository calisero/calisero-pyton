"""Update the reason of an opt-out.

CALISERO_API_KEY=... python examples/optouts/update_optout.py <opt-out-id>
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, NotFoundError, SmsClient, ValidationError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    opt_out_id = sys.argv[1] if len(sys.argv) > 1 else "019999b5-5687-71cd-ae81-baf6eea9d86f"
    client = SmsClient.create(API_KEY)

    print("=== Update OptOut ===\n")

    try:
        print("1️⃣ Checking current opt-out status...")
        current = client.opt_outs.get(opt_out_id).data

        print("✅ Current opt-out found:")
        print(f"   📱 Phone: {current.phone}")
        print(f"   📝 Current reason: {current.reason or 'Not specified'}")
        print(f"   ⏰ Created: {current.created_at}")
        print(f"   🔄 Last updated: {current.updated_at}\n")

        print("2️⃣ Updating opt-out reason...")
        updated = client.opt_outs.update(
            opt_out_id,
            phone=current.phone,
            reason="Updated: Customer called support and confirmed they want to remain opted out",
        ).data

        print("✅ Opt-out updated successfully!")
        print(f"🆔 OptOut ID: {updated.id}")
        print(f"📱 Phone Number: {updated.phone}")
        print(f"📝 Updated Reason: {updated.reason}")
        print(f"🔄 Updated: {updated.updated_at}")
    except NotFoundError:
        print(f"❌ No opt-out found for {opt_out_id}")
        print("💡 You need to create an opt-out first before updating it")
    except ValidationError as error:
        print(f"❌ Validation error: {error.message}")

        for field, messages in error.validation_errors.items():
            print(f"  - {field}: {', '.join(messages)}")
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")


if __name__ == "__main__":
    main()
