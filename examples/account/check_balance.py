"""Check the credit and the daily sending limit before a campaign.

CALISERO_API_KEY=... CALISERO_ACCOUNT_ID=... python examples/account/check_balance.py
"""

from __future__ import annotations

import os
import sys

from calisero import AccountStatus, ApiError, NotFoundError, SmsClient, UnauthorizedError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"

# An average price of an SMS part, to estimate what the credit covers: use your own pricing
AVERAGE_COST_PER_SMS = 0.05


def main() -> None:
    account_id = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("CALISERO_ACCOUNT_ID") or "9d0e0bd3-c805-4dd0-bafb-07c5ded0a8e1"
    )

    print("=== Account Balance Check ===\n")

    try:
        account = SmsClient.create(API_KEY).accounts.get(account_id).data
    except UnauthorizedError as error:
        print(f"❌ Authentication error: {error.message}")
        print("💡 Please verify your API key is valid and not expired")

        return
    except NotFoundError as error:
        print(f"❌ Account not found: {error.message}")
        print(f"💡 Please verify the account ID '{account_id}' is correct")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    credit, daily_limit, daily_remaining = account.credit, account.daily_limit, account.daily_remaining

    print("💰 Account Balance Information")
    print(f"📋 Account: {account.name} (ID: {account.id})")
    print(f"💳 Current Credit: {credit}")
    print(f"📊 Account Status: {account.status}")
    print(f"🧪 Environment: {'Sandbox' if account.sandbox else 'Production'}\n")

    print("📈 Balance Analysis:")

    if credit > 100:
        print("  🟢 Status: EXCELLENT - healthy for regular SMS operations")
    elif credit > 50:
        print("  🟡 Status: GOOD - consider topping up for high-volume campaigns")
    elif credit > 10:
        print("  🟠 Status: LOW - top up your account soon")
    else:
        print("  🔴 Status: CRITICAL - top up immediately to maintain service")

    estimated_messages = int(credit // AVERAGE_COST_PER_SMS)

    print("\n📱 Estimated Message Capacity:")
    print(f"  💸 Estimated cost per SMS: {AVERAGE_COST_PER_SMS}")
    print(f"  📊 Approximate messages remaining: ~{estimated_messages}")

    print("\n📆 Daily Sending Limit:")

    if daily_limit is None:
        print("  ✅ No daily limit applies to this account")
    else:
        print(f"  📊 Limit: {daily_limit} messages a day (resets at midnight, Romania time)")
        print(f"  📤 Sent today: {account.sent_today}")
        print(f"  📥 Left today: {daily_remaining}")

        if daily_remaining == 0:
            print("  🔴 The limit is reached: new messages are refused until midnight")
        elif daily_remaining is not None and daily_remaining < daily_limit * 0.2:
            print("  🟠 Less than 20% of the limit is left for today")

        if daily_remaining is not None and daily_remaining < estimated_messages:
            print("  💡 The daily limit, not the credit, caps what you can send today")

    print("\n🔍 Service Readiness Check:")
    issues: list[str] = []

    if credit <= 0:
        issues.append("Insufficient credit balance")

    if daily_remaining == 0:
        issues.append("Daily sending limit reached until midnight, Romania time")

    if account.status != AccountStatus.ACTIVE:
        issues.append(f"Account status is {account.status}, not active")

    if not issues:
        print("  ✅ All systems ready for SMS operations")
    else:
        print("  ❌ Issues detected:")

        for issue in issues:
            print(f"    - {issue}")


if __name__ == "__main__":
    main()
