"""List the verifications, newest first, optionally only the verified or the unverified ones.

CALISERO_API_KEY=... python examples/verifications/list_verifications.py [page] [verified|unverified]
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    page_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    status = sys.argv[2] if len(sys.argv) > 2 else None

    print("=== List Verifications ===\n")

    try:
        page = SmsClient.create(API_KEY).verifications.list(page=page_number, status=status)
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ Verifications listed successfully!")
    print(f"📊 Total on page: {len(page.data)}")
    print(f"📄 Current page: {page.meta.current_page}")
    print(f"📄 Per page: {page.meta.per_page}")
    print(f"📄 From record: {page.meta.from_ or 'N/A'}")
    print(f"📄 To record: {page.meta.to or 'N/A'}\n")

    if page.data:
        print("📝 Recent verifications:")

        for index, verification in enumerate(page.data[:5], start=1):
            print(
                f"  {index}. ✅ {verification.id} | {verification.phone} | {verification.status}"
                f" | attempts: {verification.attempts} | expired: {'yes' if verification.expired else 'no'}"
            )

        if len(page.data) > 5:
            print(f"  ... and {len(page.data) - 5} more verifications")
    else:
        print("📭 No verifications found")

    if page.has_next_page:
        print(f"\n💡 Tip: run it with the page {page.meta.current_page + 1} to fetch the next page.")


if __name__ == "__main__":
    main()
