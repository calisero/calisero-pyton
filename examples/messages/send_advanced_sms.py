"""Send an SMS with every option.

A body shown masked, a validity, a scheduled time, a delivery status callback, a
sender ID and URL shortening.

    CALISERO_API_KEY=... CALISERO_TEST_PHONE=+40742123456 python examples/messages/send_advanced_sms.py
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from calisero import ApiError, DailyLimitExceededError, SmsClient, ValidationError

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"
RECIPIENT = os.environ.get("CALISERO_TEST_PHONE") or "+40742***350"


def main() -> None:
    print("=== Send Advanced SMS ===\n")

    try:
        response = SmsClient.create(API_KEY).messages.create(
            recipient=RECIPIENT,
            body="Your code is 123456. Manage alerts: https://yourapp.com/account/alerts",
            # What the API shows instead of the body in its answers and in the dashboard
            visible_body="Your code is ******. Manage alerts: https://yourapp.com/account/alerts",
            validity=24,  # hours
            # A timezone-aware datetime is converted to the Romania time the API expects
            schedule_at=datetime.now(timezone.utc) + timedelta(hours=1),
            callback_url="https://yourapp.com/webhooks/sms",
            # One of your approved sender IDs; leave it out for the default sender
            sender="Calisero",
            shorten_urls=True,
        )
    except ValidationError as error:
        print(f"❌ Validation error: {error.message}")

        for field, messages in error.validation_errors.items():
            print(f"  - {field}: {', '.join(messages)}")

        return
    except DailyLimitExceededError as error:
        print(f"❌ Daily sending limit reached: {error.message}")
        print(f"⏰ Sending resumes at: {error.resets_at or 'midnight, Romania time'}")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    message = response.data

    print("✅ Advanced message sent successfully!")
    print(f"📨 Message ID: {message.id}")
    print(f"📱 Recipient: {message.recipient}")
    print(f"💬 Body: {message.body}")
    print(f"📊 Status: {message.status}")
    print(f"🧩 Parts: {message.parts}")
    print(f"⏰ Created: {message.created_at}")
    print(f"📅 Scheduled: {message.scheduled_at or 'Send immediately'}")
    print(f"🔗 Callback URL: {message.callback_url or 'None'}")
    print(f"👤 Sender: {message.sender or 'Default'}")

    # The links of the body that were replaced by short ones
    print(f"✂️ Shortened URLs: {len(message.shortened_urls) or 'None'}")

    for link in message.shortened_urls:
        print(f"  - {link.shortened_link} → {link.original_link}")

    # What the answer's headers report: trace ID and the account's daily sending limit
    meta = response.response_meta
    print(f"🆔 Trace ID: {meta.trace_id or 'N/A'}")

    if meta.daily_limit is not None:
        print(f"📊 Daily limit: {meta.daily_remaining} of {meta.daily_limit} messages left today")


if __name__ == "__main__":
    main()
