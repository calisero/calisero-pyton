"""Send a simple SMS message.

CALISERO_API_KEY=... CALISERO_TEST_PHONE=+40742123456 python examples/messages/send_simple_sms.py
"""

from __future__ import annotations

import os

from calisero import ApiError, SmsClient, ValidationError

# Your API key, from the dashboard's API Keys section
API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"
RECIPIENT = os.environ.get("CALISERO_TEST_PHONE") or "+40742***350"


def main() -> None:
    print("=== Send Simple SMS ===\n")

    try:
        response = SmsClient.create(API_KEY).messages.create(
            recipient=RECIPIENT,
            body="Hello from Calisero! This is a simple test message.",
        )
    except ValidationError as error:
        print(f"❌ Validation error: {error.message}")

        for field, messages in error.validation_errors.items():
            print(f"  - {field}: {', '.join(messages)}")

        return
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    message = response.data

    print("✅ Message sent successfully!")
    print(f"📨 Message ID: {message.id}")
    print(f"📱 Recipient: {message.recipient}")
    print(f"💬 Body: {message.body}")
    print(f"📊 Status: {message.status}")
    print(f"🧩 Parts: {message.parts}")
    print(f"⏰ Created: {message.created_at}")
    print(f"🆔 Trace ID: {response.response_meta.trace_id or 'N/A'}")


if __name__ == "__main__":
    main()
