"""Send the same message to several recipients, one request each.

It stops once the account's daily sending limit is used up.

    CALISERO_API_KEY=... python examples/messages/send_bulk_sms.py
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from calisero import ApiError, DailyLimitExceededError, SmsClient, ValidationError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"

RECIPIENTS = ["+40742***350", "+40742***351", "+40742***352", "+40742***353", "+40742***354"]
BODY = "Important announcement: Our office will be closed tomorrow for maintenance. Thank you for your understanding."
CALLBACK_URL = "https://yourapp.com/webhooks/bulk-sms"


@dataclass
class Result:
    recipient: str
    status: str
    message_id: str | None = None
    parts: int | None = None
    error: str | None = None


def main() -> None:
    # One client for all the requests
    client = SmsClient.create(API_KEY)
    results: list[Result] = []
    success_count = failure_count = 0

    print("=== Send Bulk SMS Messages ===\n")
    print(f"📱 Sending messages to {len(RECIPIENTS)} recipients...\n")

    for index, recipient in enumerate(RECIPIENTS):
        print(f"Sending to {recipient}... ", end="")

        try:
            response = client.messages.create(recipient=recipient, body=BODY, validity=24, callback_url=CALLBACK_URL)
        except DailyLimitExceededError as error:
            # Nothing was sent or billed, and every further message would be refused too
            print("❌ Daily sending limit reached")
            print(f"  💬 Error: {error.message}\n")
            results.append(Result(recipient, "daily_limit_exceeded", error=error.message))
            failure_count += 1
            break
        except ValidationError as error:
            print("❌ Validation error")
            print(f"  💬 Error: {error.message}\n")
            results.append(Result(recipient, "validation_error", error=error.message))
            failure_count += 1
            continue
        except ApiError as error:
            print("❌ API error")
            print(f"  💬 Error: {error.message}")
            print(f"  🔢 Status: {error.status_code or 'N/A'}")
            print(f"  🆔 Trace ID: {error.trace_id or 'N/A'}\n")
            results.append(Result(recipient, "api_error", error=error.message))
            failure_count += 1
            continue

        message = response.data
        print("✅ Success")
        print(f"  📨 Message ID: {message.id}")
        print(f"  📊 Status: {message.status}")

        # What is left of the account's daily sending limit (None when it has none)
        daily_remaining = response.response_meta.daily_remaining

        if daily_remaining is not None:
            print(f"  📉 Daily limit: {daily_remaining} messages left today")

        print()
        results.append(Result(recipient, "success", message_id=message.id, parts=message.parts))
        success_count += 1

        # Every further message would be refused until midnight, Romania time
        if daily_remaining == 0:
            print("⛔ Daily sending limit used up: the remaining recipients are skipped\n")
            break

        # Stay well under the request rate limit (240 requests a minute)
        if index < len(RECIPIENTS) - 1:
            time.sleep(0.25)

    print("=== Bulk SMS Summary ===")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failure_count}")
    print(f"⏭️ Skipped: {len(RECIPIENTS) - success_count - failure_count}")
    print(f"📊 Total: {len(RECIPIENTS)}")
    print(f"📈 Success Rate: {success_count / len(RECIPIENTS) * 100:.2f}%\n")

    print("📝 Detailed Results:")

    for result in results:
        if result.status == "success":
            outcome = f"✅ Sent (ID: {result.message_id}, Parts: {result.parts})"
        else:
            outcome = f"❌ {result.status} - {result.error}"

        print(f"  📱 {result.recipient}: {outcome}")

    if success_count > 0:
        print(f"\n💡 Tip: Monitor the callback URL '{CALLBACK_URL}' for delivery updates")


if __name__ == "__main__":
    main()
