"""Cancel a scheduled message: schedule one for tomorrow, then delete it.

CALISERO_API_KEY=... CALISERO_TEST_PHONE=+40742123456 python examples/messages/delete_sms.py
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from calisero import ApiError, ForbiddenError, NotFoundError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"
RECIPIENT = os.environ.get("CALISERO_TEST_PHONE") or "+40742***350"


def main() -> None:
    client = SmsClient.create(API_KEY)

    print("=== Delete SMS Message ===\n")

    try:
        print("1️⃣ Creating a scheduled message for deletion demo...")
        message = client.messages.create(
            recipient=RECIPIENT,
            body="This message will be deleted before sending.",
            schedule_at=datetime.now(timezone.utc) + timedelta(days=1),  # tomorrow
        ).data

        print("✅ Scheduled message created!")
        print(f"📨 Message ID: {message.id}")
        print(f"📅 Scheduled for: {message.scheduled_at}")
        print(f"📊 Status: {message.status}\n")

        print("2️⃣ Deleting the scheduled message...")
        client.messages.delete(message.id)

        print("✅ Message deleted successfully!")
        print(f"💡 The message '{message.id}' has been cancelled and will not be sent")

        print("\n3️⃣ Verifying deletion...")

        try:
            client.messages.get(message.id)
            print("⚠️ Message still exists")
        except NotFoundError:
            print("✅ Confirmed: a cancelled message is no longer found")
    except ForbiddenError as error:
        print(f"❌ Cannot delete message: {error.message}")
        print("💡 Only scheduled messages that have not been sent can be deleted")
        print("💡 Messages already queued, sent or delivered cannot be deleted")
    except NotFoundError as error:
        print(f"❌ Message not found: {error.message}")
        print("💡 The message may have already been deleted or doesn't exist")
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")


if __name__ == "__main__":
    main()
