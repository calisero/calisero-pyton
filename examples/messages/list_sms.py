"""List the messages, newest first, 50 a page.

CALISERO_API_KEY=... python examples/messages/list_sms.py [page]
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    page_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    client = SmsClient.create(API_KEY)

    print("=== List SMS Messages ===\n")

    try:
        page = client.messages.list(page=page_number)

        print("✅ Messages listed successfully!")
        print(f"📊 Messages on this page: {len(page.data)}")
        print(f"📄 Current page: {page.meta.current_page}")
        print(f"📄 Per page: {page.meta.per_page}")
        print(f"📄 From record: {page.meta.from_ or 'N/A'}")
        print(f"📄 To record: {page.meta.to or 'N/A'}\n")

        if page.data:
            print("📝 Recent messages:")

            for index, message in enumerate(page.data[:5], start=1):
                body = f"{message.body[:30]}..." if len(message.body) > 30 else message.body
                print(f"  {index}. 📨 {message.id} -> {message.recipient}: {body} [{message.status}]")

            if len(page.data) > 5:
                print(f"  ... and {len(page.data) - 5} more messages")
        else:
            print("📭 No messages found")

        print("\n🔗 Pagination:")
        print(f"  - Previous page: {'Available' if page.links.prev else 'N/A'}")
        print(f"  - Next page: {'Available' if page.links.next else 'N/A'}")

        if page.has_next_page:
            print("\n📄 Getting next page...")
            following = client.messages.list(page=page.meta.current_page + 1)
            print(f"✅ Next page retrieved with {len(following.data)} messages")
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")


if __name__ == "__main__":
    main()
