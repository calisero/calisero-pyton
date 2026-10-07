"""Retrieve a message and its delivery status.

CALISERO_API_KEY=... python examples/messages/get_sms.py <message-id>
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, NotFoundError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    message_id = sys.argv[1] if len(sys.argv) > 1 else "9e2574e8-3615-4090-9b5a-0fc812079da8"

    print("=== Get SMS Message ===\n")

    try:
        message = SmsClient.create(API_KEY).messages.get(message_id).data
    except NotFoundError as error:
        print(f"❌ Message not found: {error.message}")
        print(f"💡 Please check if the message ID '{message_id}' exists")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ Message retrieved successfully!")
    print(f"📨 Message ID: {message.id}")
    print(f"📱 Recipient: {message.recipient}")
    print(f"💬 Body: {message.body}")
    print(f"📊 Status: {message.status}")
    print(f"🧩 Parts: {message.parts}")
    print(f"⏰ Created: {message.created_at}")
    print(f"📅 Scheduled: {message.scheduled_at or 'Sent immediately'}")
    print(f"📤 Sent: {message.sent_at or 'Not sent yet'}")
    print(f"📥 Delivered: {message.delivered_at or 'Not delivered yet'}")
    print(f"🔗 Callback URL: {message.callback_url or 'None'}")
    print(f"👤 Sender: {message.sender or 'Default'}")

    for link in message.shortened_urls:
        print(f"✂️ {link.shortened_link}: {link.click_count} clicks, last {link.last_click or 'never'}")


if __name__ == "__main__":
    main()
