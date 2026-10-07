"""List the opt-outs, 50 a page.

CALISERO_API_KEY=... python examples/optouts/list_optouts.py [page]
"""

from __future__ import annotations

import os
import sys

from calisero import ApiError, SmsClient

API_KEY = os.environ.get("CALISERO_API_KEY") or "your-api-key-here"


def main() -> None:
    page_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    print("=== List OptOuts ===\n")

    try:
        page = SmsClient.create(API_KEY).opt_outs.list(page=page_number)
    except ApiError as error:
        print(f"❌ API error: {error.message}")
        print(f"🔢 Status Code: {error.status_code or 'N/A'}")
        print(f"🆔 Trace ID: {error.trace_id or 'N/A'}")

        return

    print("✅ OptOuts listed successfully!")
    print(f"📊 OptOuts on this page: {len(page.data)}")
    print(f"📄 Current page: {page.meta.current_page}")
    print(f"📄 Per page: {page.meta.per_page}")
    print(f"📄 From record: {page.meta.from_ or 'N/A'}")
    print(f"📄 To record: {page.meta.to or 'N/A'}\n")

    if page.data:
        print("🚫 Current opt-outs:")

        for index, opt_out in enumerate(page.data[:10], start=1):
            if opt_out.reason is None:
                reason = "No reason provided"
            else:
                reason = f"{opt_out.reason[:40]}..." if len(opt_out.reason) > 40 else opt_out.reason

            print(f"  {index}. 📱 {opt_out.phone} [ID: {opt_out.id}]")
            print(f"     📝 {reason}")
            print(f"     ⏰ {opt_out.created_at}\n")

        if len(page.data) > 10:
            print(f"  ... and {len(page.data) - 10} more opt-outs\n")

        with_reasons = sum(1 for opt_out in page.data if opt_out.reason is not None)
        print("📊 Statistics for this page:")
        print(f"  - With reasons: {with_reasons}")
        print(f"  - Without reasons: {len(page.data) - with_reasons}")
    else:
        print("✅ No opt-outs found - all numbers can receive messages")

    print("\n🔗 Pagination:")
    print(f"  - Previous page: {'Available' if page.links.prev else 'N/A'}")
    next_page = f"python examples/optouts/list_optouts.py {page_number + 1}" if page.links.next else "N/A"
    print(f"  - Next page: {next_page}")


if __name__ == "__main__":
    main()
