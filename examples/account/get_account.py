"""Retrieve the account: details, credit, status and daily sending limit.

CALISERO_API_KEY=... CALISERO_ACCOUNT_ID=... python examples/account/get_account.py
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, NotFoundError, SmsClient, UnauthorizedError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    # The account's ID, shown in the dashboard
    account_id = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("CALISERO_ACCOUNT_ID") or "9d0e0bd3-c805-4dd0-bafb-07c5ded0a8e1"
    )

    print("=== Get Account Information ===\n")

    try:
        account = SmsClient.create(API_KEY).accounts.get(account_id).data
    except UnauthorizedError as error:
        print(f"❌ Authentication error: {error.message}")
        print("💡 Please check your API key and ensure it's valid")

        return
    except NotFoundError as error:
        print(f"❌ Account not found: {error.message}")
        print(f"💡 Please check if the account ID '{account_id}' is correct")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ Account information retrieved successfully!\n")

    print("📋 Basic Information:")
    print(f"  🆔 Account ID: {account.id}")
    print(f"  🏷️ Account Code: {account.code}")
    print(f"  👤 Name: {account.name}")
    print(f"  📝 Description: {account.description or 'Not provided'}")
    print(f"  📧 Email: {account.email or 'Not provided'}")
    print(f"  📞 Phone: {account.phone or 'Not provided'}")
    print(f"  👨‍💼 Contact Person: {account.contact_person or 'Not provided'}\n")

    print("💰 Financial Information:")
    print(f"  💳 Current Credit: {account.credit}")
    print(f"  🏦 IBAN: {account.iban or 'Not provided'}")
    print(f"  📄 Fiscal Code: {account.fiscal_code or 'Not provided'}")
    print(f"  📋 Registry Number: {account.registry_number or 'Not provided'}\n")

    print("📍 Address Information:")
    print(f"  🏠 Address: {account.address or 'Not provided'}")
    print(f"  🏙️ City: {account.city or 'Not provided'}")
    print(f"  🗺️ State: {account.state or 'Not provided'}")
    print(f"  🌍 Country: {account.country or 'Not provided'}")
    print(f"  📮 Postal Code: {account.postal_code or 'Not provided'}\n")

    print("⚙️ Account Status:")
    print(f"  📊 Status: {account.status}")
    print(f"  🧪 Sandbox Mode: {'Yes' if account.sandbox else 'No'}")
    print(f"  ⏰ Created: {account.created_at}\n")

    print("📆 Daily Sending Limit:")
    print(f"  📊 Daily Limit: {account.daily_limit if account.daily_limit is not None else 'None'}")
    print(f"  📥 Left Today: {account.daily_remaining if account.daily_remaining is not None else 'Unlimited'}")
    print(f"  📤 Sent Today: {account.sent_today}")

    if account.sandbox:
        print("\n🧪 SANDBOX NOTICE:")
        print("  This account is in sandbox mode: its messages are test messages,")
        print("  marked delivered at once, never sent to a phone nor billed.")


if __name__ == "__main__":
    main()
