# SMS API Examples

This directory contains runnable examples for every operation of the Calisero SMS API Python library. They are
organized by functionality and demonstrate proper error handling.

## Directory Structure

```
examples/
├── messages/                       # SMS message operations
│   ├── send_simple_sms.py          # Send a basic SMS message
│   ├── send_advanced_sms.py        # Every option: scheduling, callbacks, sender, URL shortening
│   ├── send_bulk_sms.py            # Several recipients, within the daily limit
│   ├── get_sms.py                  # Retrieve a message and its delivery status
│   ├── list_sms.py                 # List messages with pagination
│   └── delete_sms.py               # Cancel a scheduled message
├── optouts/                        # Opt-out management
│   ├── create_optout.py            # Opt a phone number out
│   ├── get_optout.py               # Retrieve an opt-out
│   ├── list_optouts.py             # List the opt-outs with pagination
│   ├── update_optout.py            # Update an opt-out's reason
│   └── delete_optout.py            # Remove an opt-out (re-enable SMS)
├── verifications/                  # Phone verifications (OTP)
│   ├── create_verification.py      # Start a verification (send a code)
│   ├── get_verification.py         # Retrieve a verification
│   ├── list_verifications.py       # List verifications with pagination and a status filter
│   └── validate_verification.py    # Validate a code
├── account/                        # Account information
│   ├── get_account.py              # Account details
│   └── check_balance.py            # Credit, daily limit and readiness
├── webhooks/                       # Callbacks Calisero sends to your application
│   └── delivery_webhook.py         # Receive delivery status callbacks
└── error_handling_complete.py      # Every exception class and how to handle it
```

## Quick Start

1. **Install the library** (from the repository, the examples import it as `calisero`):
   ```bash
   uv sync
   ```
   or, in a virtual environment of your own, `pip install calisero`.

2. **Set your credentials** in the environment:
   - `CALISERO_API_KEY`: your API key (a sandbox key sends no real message and costs nothing)
   - `CALISERO_TEST_PHONE`: the phone number to send to, in E.164 format (e.g. `+40742123456`)
   - `CALISERO_ACCOUNT_ID`: your account ID, for the account examples

3. **Run an example:**
   ```bash
   CALISERO_API_KEY=your-api-key-here uv run python examples/messages/send_simple_sms.py
   ```

   The examples that read a resource take its ID as an argument:
   ```bash
   uv run python examples/messages/get_sms.py 9e2574e8-3615-4090-9b5a-0fc812079da8
   ```

## Phone Number Format

Without `CALISERO_TEST_PHONE`, the examples use masked phone numbers like `+40742***350`, which the API refuses.
Phone numbers must be mobile numbers in international E.164 format, starting with `+` (e.g. `+40742123350`).

## Error Handling

Each example handles the errors it can meet:

- **Authentication errors** (401) - Invalid or revoked API key
- **Validation errors** (422) - Invalid request data, an opted-out recipient
- **Not found errors** (404) - Non-existent resources
- **Daily sending limit** (429) - The account sent its daily limit; nothing is sent until midnight, Romania time
- **Rate limiting** (429) - More than 240 requests a minute
- **Server errors** (5xx) - API server issues
- **Transport errors** - No answer: network error or timeout

For comprehensive error handling patterns, see `error_handling_complete.py`.

## Webhook Example

`webhooks/delivery_webhook.py` starts a server (the standard library's `wsgiref`) that receives the delivery status
callbacks, with the library's `DeliveryWebhookHandler`:

```bash
CALISERO_WEBHOOK_TOKEN=s3cr3t uv run python examples/webhooks/delivery_webhook.py

curl -X POST 'http://localhost:8080/webhooks/calisero?token=s3cr3t' -H 'Content-Type: application/json' \
     -d '{"messageId":"019961db-14a7-7348-963f-5a7a789a969f","recipient":"+40742***350","status":"delivered","price":0.0378}'
```

The server listens on `127.0.0.1:8080`; set `PORT` to use another port, and `HOST=0.0.0.0` to reach it from outside a
container.

## Best Practices Demonstrated

1. **Proper Error Handling** - Specific exception classes first, then `ApiError`
2. **Trace ID Logging** - Trace IDs for support and the dashboard's Developers → Debug page
3. **Rate Limiting** - A delay between the requests of a bulk send
4. **Daily Limit** - Stopping a bulk send once the daily sending limit is used up
5. **Secure Logging** - `visible_body` to keep codes out of the API's answers and the dashboard
6. **Pagination** - Reading the following pages
7. **Webhook Security** - A secret token in the callback URL

## Testing

CI checks every example: it compiles and imports only names the package exports (`scripts/check_examples.py`), and
its use of the library type-checks (`mypy`, strict):

```bash
uv run python scripts/check_examples.py
uv run mypy
```

## Contributing

When adding new examples:

1. Follow the existing directory structure
2. Put the code in a `main()` function, run under `if __name__ == "__main__":`
3. Include error handling for the errors the operation can meet
4. Read credentials from the environment, never hard-code them
5. Use masked phone numbers as defaults
6. Run `uv run python scripts/check_examples.py` and `uv run mypy`
7. Update this README and the main README
