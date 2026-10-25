# Calisero Python SMS API Library

[![PyPI version](https://img.shields.io/pypi/v/calisero.svg?style=flat-square)](https://pypi.org/project/calisero/)
[![CI](https://img.shields.io/github/actions/workflow/status/calisero/calisero-pyton/ci.yml?branch=main&label=tests&style=flat-square)](https://github.com/calisero/calisero-pyton/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/calisero/calisero-pyton?style=flat-square)](https://codecov.io/gh/calisero/calisero-pyton)
[![Python](https://img.shields.io/pypi/pyversions/calisero.svg?style=flat-square)](https://pypi.org/project/calisero/)
[![Typed](https://img.shields.io/badge/typing-mypy%20strict-2a6db2.svg?style=flat-square)](https://mypy-lang.org)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg?style=flat-square)](pyproject.toml)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-d7ff64.svg?style=flat-square)](https://docs.astral.sh/ruff/)
[![License](https://img.shields.io/pypi/l/calisero.svg?style=flat-square)](LICENSE.md)
[![Downloads](https://img.shields.io/pypi/dm/calisero.svg?style=flat-square)](https://pypi.org/project/calisero/)

**Official Python library for the [Calisero](https://calisero.ro) transactional SMS API.**

Send SMS messages, verify phone numbers with one-time codes, manage opt-outs for GDPR compliance, receive delivery reports and monitor your account, with a fully typed library that has no dependencies.

## Features

- 🚀 **Simple & Intuitive**: `SmsClient.create(api_key)`, then `client.messages.create(recipient=..., body=...)`
- 🔒 **Type Safe**: fully typed, `py.typed` included, checked with `mypy --strict`
- 🌐 **Zero Dependencies**: built on `urllib` from the standard library, nothing else to install
- 🧱 **Immutable Models**: frozen dataclasses with the API's own field names
- 📱 **Complete API Coverage**: messages, verifications (OTP), opt-outs and accounts, checked against the API's OpenAPI document
- 🔐 **OTP / 2FA**: start a verification and validate the code in two calls
- ✂️ **URL Shortening**: shorten the links of a message body and track their clicks
- 📊 **Limits & Tracing**: daily sending limit, request rate limit and the trace ID of every answer and error
- 📬 **Delivery Webhooks**: validated parsing of delivery status callbacks, and a ready handler for Flask, Django, FastAPI or any WSGI server
- 🛡️ **Error Handling**: an exception class for every kind of failure, with the API's message and the trace ID
- 🕐 **Romania Time Handled**: pass a timezone-aware `datetime` to schedule a message, it is converted to the time zone the API expects
- 🧪 **Thoroughly Tested**: unit, integration (real HTTP), contract (OpenAPI) and package smoke tests on Python 3.10 to 3.14, Linux, macOS and Windows, 100% coverage
- 📖 **Rich Examples**: 19 runnable examples covering every operation
- 🐘 **Sibling Libraries**: [`calisero/calisero-php`](https://github.com/calisero/calisero-php), [`calisero/laravel-sms`](https://github.com/calisero/laravel-sms), [`calisero/calisero-symfony`](https://github.com/calisero/calisero-symfony) and [`@calisero/calisero-node`](https://github.com/calisero/calisero-node-js)

## Requirements

- Python **3.10 or later** — tested on **3.10, 3.11, 3.12, 3.13 and 3.14**
- A Calisero API key

The library carries no runtime dependency: its HTTP client is `urllib`, from the standard library. It is meant for
server-side code: never ship your API key to a browser or a mobile app.

## Installation

```bash
pip install calisero
```

With other package managers: `uv add calisero`, `poetry add calisero`.

## Getting Your API Key

To use this library, you'll need an API key from your Calisero account:

1. **Log in to your Calisero account** at [https://calisero.ro](https://calisero.ro)
2. **Navigate to the dashboard** and go to the **"API Keys"** section
3. **Click "Add Key"** to create a new API key
4. **Configure your key:**
   - Give it a descriptive name (e.g., "Production App", "Development")
   - Set IP filters if needed for additional security
   - Choose a sandbox key to test without sending or paying for real messages
5. **Copy your API key** and store it securely

> **Security Note**: Never commit API keys to version control. Use environment variables or a secret manager.

## Quick Start

### Basic SMS Sending

```python
import os

from calisero import SmsClient

# Create the SMS client
client = SmsClient.create(os.environ["CALISERO_API_KEY"])

# Send a simple SMS
message = client.messages.create(recipient="+40742***350", body="Hello from Calisero!").data

print(f"Message sent! ID: {message.id}")
print(f"Status: {message.status}")
```

### Environment Configuration

For production applications, store your API key securely:

```bash
# .env file, or your platform's secret settings
CALISERO_API_KEY=your-api-key-here
```

```python
import os

from calisero import SmsClient

client = SmsClient.create(os.environ.get("CALISERO_API_KEY"))
```

`SmsClient.create()` raises a `TypeError` when the key is missing (`None`) and a `ValueError` when it is empty, so a
misconfigured environment fails at startup rather than on the first message. The whitespace around the key (the
newline of a key read from a file) is dropped.

## 🎯 Common Use Cases

### OTP / 2FA Authentication

The Verifications API generates the code, sends it by SMS and checks it, so your application never stores it:

```python
from calisero import SmsClient, ValidationError

client = SmsClient.create(os.environ["CALISERO_API_KEY"])

# 1. Send a code (6 characters, valid for 5 minutes by default)
client.verifications.create(phone="+40742***350", brand="YourApp")

# 2. Check the code the user typed
try:
    verification = client.verifications.validate(phone="+40742***350", code=user_input).data
    print(f"Verified at {verification.verified_at}")
except ValidationError as error:
    # A wrong or expired code, or too many attempts (5)
    print(error.message)
```

To send a code you generate yourself, hide it in the API's answers and in the dashboard with `visible_body`:

```python
client.messages.create(
    recipient=user_phone_number,
    body="Your verification code is: AC3-4F6. Valid for 5 minutes.",
    visible_body="Your verification code is: ******. Valid for 5 minutes.",
    sender="YourApp",
)
```

### Order Notifications

```python
client.messages.create(
    recipient=customer_phone,
    body=f"Order #{order_number} confirmed! Estimated delivery: {delivery_date}",
    callback_url="https://yourstore.com/webhooks/sms/dlr",
    sender="YourStore",
)
```

### Marketing Campaigns with Opt-out Compliance

The API refuses to send to a number that opted out: the message fails validation (422) and is neither sent nor
billed.

```python
from calisero import ValidationError

try:
    client.messages.create(
        recipient=phone_number,
        body="Special offer! Get 20% off with code SAVE20. Reply STOP to opt out.",
        sender="YourBrand",
    )
except ValidationError as error:
    if "recipient" not in error.validation_errors:
        raise

    print(f"Not sent to {phone_number}: {' '.join(error.validation_errors['recipient'])}")

# When a customer asks to stop receiving messages
client.opt_outs.create(phone=phone_number, reason="Replied STOP")
```

### Advanced Message Creation

```python
from datetime import datetime, timezone

response = client.messages.create(
    recipient="+40742***350",
    body="Your code is 123456. Manage alerts: https://yoursite.com/alerts",
    visible_body="Your code is ******. Manage alerts: https://yoursite.com/alerts",  # Shown in answers and the dashboard
    validity=24,  # Validity period, in hours
    schedule_at=datetime(2026, 12, 25, 8, 0, tzinfo=timezone.utc),  # Sent at 10:00, Romania time
    callback_url="https://yoursite.com/webhook",  # Delivery reports
    sender="Calisero",  # One of your approved sender IDs
    shorten_urls=True,  # Shorten the links of the body
)
```

`schedule_at` takes a timezone-aware `datetime`, converted to the Romania time the API reads, or a
`YYYY-MM-DD HH:MM:SS` string already in Romania time. A naive `datetime` is refused with a `ValueError`: which time
zone it is in cannot be known. A time already past today sends the message at once; the API refuses an earlier day,
and accepts up to 5 years ahead.

## Authentication

### Using an API Key

```python
client = SmsClient.create("your-api-key-here")
```

### Custom Authentication Provider

Pass an object with a `get_token()` method instead of the key: it is called before every request, e.g. to read the
key from a secret manager and rotate it without a restart.

```python
from calisero import SmsClient


class VaultToken:
    def get_token(self) -> str:
        return secret_manager.read("calisero-api-key")


client = SmsClient.create(VaultToken())
```

## 📚 Examples

This library includes runnable examples for every operation in the [`examples/`](examples/) directory:

### 📱 Message Examples
- **[`examples/messages/send_simple_sms.py`](examples/messages/send_simple_sms.py)** - Send a basic SMS message
- **[`examples/messages/send_advanced_sms.py`](examples/messages/send_advanced_sms.py)** - Scheduling, callbacks, custom sender and URL shortening
- **[`examples/messages/send_bulk_sms.py`](examples/messages/send_bulk_sms.py)** - Several recipients, stopping at the daily sending limit
- **[`examples/messages/get_sms.py`](examples/messages/get_sms.py)** - Retrieve a message and its delivery status
- **[`examples/messages/list_sms.py`](examples/messages/list_sms.py)** - List messages with pagination
- **[`examples/messages/delete_sms.py`](examples/messages/delete_sms.py)** - Cancel a scheduled message

### 🚫 Opt-out Examples (GDPR Compliance)
- **[`examples/optouts/create_optout.py`](examples/optouts/create_optout.py)** - Opt a phone number out
- **[`examples/optouts/get_optout.py`](examples/optouts/get_optout.py)** - Retrieve an opt-out
- **[`examples/optouts/list_optouts.py`](examples/optouts/list_optouts.py)** - List the opt-outs with pagination
- **[`examples/optouts/update_optout.py`](examples/optouts/update_optout.py)** - Update an opt-out's reason
- **[`examples/optouts/delete_optout.py`](examples/optouts/delete_optout.py)** - Remove an opt-out (re-enable SMS)

### ✅ Verification Examples (OTP)
- **[`examples/verifications/create_verification.py`](examples/verifications/create_verification.py)** - Start a verification (send a code)
- **[`examples/verifications/get_verification.py`](examples/verifications/get_verification.py)** - Retrieve a verification
- **[`examples/verifications/list_verifications.py`](examples/verifications/list_verifications.py)** - List verifications with pagination and a status filter
- **[`examples/verifications/validate_verification.py`](examples/verifications/validate_verification.py)** - Validate a code

### 👤 Account Examples
- **[`examples/account/get_account.py`](examples/account/get_account.py)** - Account details
- **[`examples/account/check_balance.py`](examples/account/check_balance.py)** - Credit and daily sending limit, with an analysis

### 📬 Webhook Examples
- **[`examples/webhooks/delivery_webhook.py`](examples/webhooks/delivery_webhook.py)** - Receive delivery status callbacks

### 🛡️ Error Handling
- **[`examples/error_handling_complete.py`](examples/error_handling_complete.py)** - Every exception class and how to handle it

### 🚀 Running Examples

```bash
git clone https://github.com/calisero/calisero-pyton.git
cd calisero-pyton
uv sync
CALISERO_API_KEY=your-api-key-here CALISERO_TEST_PHONE=+40742123456 uv run python examples/messages/send_simple_sms.py
```

> **Note**: Examples use masked phone numbers (`+40742***350`) unless `CALISERO_TEST_PHONE` is set. Use a sandbox API
> key to try them without sending real messages.

## API Reference

Every call is synchronous and takes its arguments as keywords, the ids of the resources excepted. A single resource
comes as an `ApiResponse` (`data`, `response_meta`), a list as a `Paginated` (`data`, `links`, `meta`,
`response_meta`). Every call also takes an optional `timeout`: seconds to wait for its answer, instead of the
client's.

### Messages

#### Send a Message

```python
response = client.messages.create(recipient="+40742***350", body="Hello World!")

message = response.data
print(message.id)  # Message UUID
print(message.status)  # 'scheduled', then 'sent', 'delivered' or 'undelivered'
print(message.parts)  # Number of SMS parts

# What the answer's headers report
print(response.response_meta.trace_id)  # The request's trace ID
print(response.response_meta.daily_remaining)  # Messages left today (None: no daily limit)
```

| Argument | Type | Description |
|---|---|---|
| `recipient` | `str` | **Required.** Mobile number in E.164 format, e.g. `+40742123456` |
| `body` | `str` | **Required.** The text, at most 1600 characters |
| `visible_body` | `str` | Shown instead of `body` in the API's answers and the dashboard |
| `validity` | `int` | Validity period, in hours |
| `schedule_at` | `datetime \| str` | When to send it: a timezone-aware `datetime`, or a `YYYY-MM-DD HH:MM:SS` string in Romania time |
| `callback_url` | `str` | Where Calisero posts the delivery status updates: a public `http(s)://` address |
| `sender` | `str` | One of your approved sender IDs, written exactly as approved; the default sender when omitted |
| `shorten_urls` | `bool` | Shorten the `http(s)://` links of the body |

The arguments left as `None` are not sent; `False` and `0` are.

- `sender` must be a sender ID already approved for your account (Messages > Senders in the dashboard), written
  exactly as approved: the match is case-sensitive. A sender that is unknown, pending or rejected is refused with a
  `ValidationError` (422) and nothing is sent. The sender IDs of the examples (`Calisero`, `YourApp`...) are
  placeholders, not senders you can use.
- `callback_url` must be an `http` or `https` address on the public Internet: private, loopback and link-local
  addresses are refused, and redirects are not followed.

#### Shorten URLs

Set `shorten_urls=True` and Calisero replaces every `http://` and `https://` link of the body with a short one before
sending, so the SMS gets shorter (and may take fewer parts). Each shortened link comes back with its click
statistics:

```python
message = client.messages.create(
    recipient="+40742***350",
    body="Your order has shipped! Track it: https://yourstore.com/orders/12345/tracking",
    shorten_urls=True,
).data

for link in message.shortened_urls:
    print(link.original_link)  # https://yourstore.com/orders/12345/tracking
    print(link.shortened_link)  # https://calisero.ro/s/ghJKPV

# Later: how many times the links were opened
for link in client.messages.get(message.id).data.shortened_urls:
    print(link.click_count, link.last_click)  # Number of clicks, last click or None
```

#### Get Message Details

```python
message = client.messages.get("message-uuid-here").data

print(message.recipient, message.body, message.status)
print(message.sent_at, message.delivered_at)
```

#### List Messages

```python
page = client.messages.list()  # Newest first, 50 a page

for message in page:  # A page iterates over its items (page.data)
    print(f"{message.id}: {message.body}")

print(f"Current page: {page.meta.current_page}")

if page.has_next_page:
    following = client.messages.list(page=page.meta.current_page + 1)
```

`page.meta` holds `current_page`, `per_page`, `path`, `from_` and `to` (the API's `from`, a Python keyword);
`page.links` the URLs of the `first`, `prev` and `next` pages.

#### Delete a Message

Only a message still scheduled can be cancelled:

```python
from calisero import ForbiddenError

try:
    client.messages.delete("message-uuid-here")
    print("Message cancelled")
except ForbiddenError:
    print("Cannot delete: the message is already queued, sent or delivered")
```

### Verifications (OTP)

#### Create a Verification

```python
response = client.verifications.create(
    phone="+40742***350",
    brand="Calisero",  # Named in the default message; required unless a template is given
    # template="Your Calisero code is {code}",  # Or a message of your own, holding {code}
    # expires_in=10,  # Minutes the code stays valid, 1 to 10 (5 by default)
)

verification = response.data
print(verification.id, verification.status)  # 'unverified'
print(verification.expires_at)

# The code's SMS counts towards the account's daily sending limit
print(response.response_meta.daily_remaining)
```

Neither the `brand` nor the `template` may contain links (web addresses, domains, emails or IP addresses): the codes
are sent from a shared sender, so the API refuses them with a `ValidationError` (422).

#### Get Verification Details

```python
verification = client.verifications.get("verification-uuid-here").data

print(verification.status)  # 'unverified' or 'verified'
print(verification.verified_at)  # Timestamp or None
print(verification.expired, verification.attempts)
```

#### List Verifications

```python
from calisero import VerificationStatus

# Optionally only the verified or the unverified ones
page = client.verifications.list(page=1, status=VerificationStatus.VERIFIED)

for verification in page:
    print(f"{verification.id} | {verification.phone} | {verification.status}")
```

#### Validate a Verification Code (OTP)

The code is checked against the latest verification of the phone number, in any case:

```python
verification = client.verifications.validate(phone="+40742***350", code="ABC123").data

print(verification.status)  # 'verified' (checking a verified code again succeeds)
```

A wrong or expired code, or a sixth attempt, raises a `ValidationError` whose `validation_errors["code"]` says which;
a phone number without a verification a `NotFoundError`.

### Opt-outs

#### Create an Opt-out

```python
opt_out = client.opt_outs.create(phone="+40742***350", reason="User requested opt-out via website").data

print(f"Opt-out created with ID: {opt_out.id}")
```

#### List Opt-outs

```python
for opt_out in client.opt_outs.list():
    print(f"{opt_out.phone}: {opt_out.reason or 'no reason'}")
```

#### Get, Update and Delete an Opt-out

```python
opt_out = client.opt_outs.get("optout-uuid-here").data

client.opt_outs.update("optout-uuid-here", phone=opt_out.phone, reason="Updated reason")

# The number can receive messages again
client.opt_outs.delete("optout-uuid-here")
```

### Accounts

```python
account = client.accounts.get("account-uuid-here").data

print(f"Account: {account.name}")
print(f"Credit: {account.credit}")
print(f"Status: {account.status}")  # 'active', 'pending' or 'disabled'
print(f"Sandbox: {'Yes' if account.sandbox else 'No'}")

# Daily sending limit (None when no daily limit applies)
print(f"Daily limit: {account.daily_limit or 'none'}")
print(f"Left today: {account.daily_remaining if account.daily_remaining is not None else 'unlimited'}")
print(f"Sent today: {account.sent_today}")
```

### Statuses

The models keep a status as the string the API sent, so a status a future API version adds still reads. The
`MessageStatus`, `VerificationStatus`, `AccountStatus` and `DeliveryStatus` string enums hold the known values:

```python
from calisero import MessageStatus

if message.status == MessageStatus.DELIVERED:
    ...
```

## Delivery Status Webhooks

When a message has a `callback_url`, Calisero posts a JSON payload to it each time the message's status changes
(`sent`, `delivered` or `undelivered`). Answer with any 2xx status within 2 seconds: only a failed connection or a
slower answer is retried (at most 5 attempts in total), a non-2xx answer is not.

`DeliveryWebhookHandler` reads and validates the payload, hands it to your `on_message` as a `DeliveryWebhookMessage`,
and tells you how to answer:

```python
import os

from calisero import DeliveryWebhookHandler, DeliveryWebhookMessage


def on_message(message: DeliveryWebhookMessage) -> None:
    print(message.message_id)  # The message's UUID
    print(message.status)  # 'sent', 'delivered' or 'undelivered'
    print(message.delivered_at)  # Set for 'delivered'
    print(message.price)  # Price charged for the message's parts
    print(message.remaining_balance)  # Account balance after billing
    print(message.daily_remaining)  # Messages left today when it was sent (None: no daily limit)
    # Keep it short (update a record, queue a job): the answer waits for it


handler = DeliveryWebhookHandler(
    on_message,
    # Optional: accept only callback URLs that carry ?token=<this secret>
    token=os.environ["CALISERO_WEBHOOK_TOKEN"],
    on_error=lambda error: print(error),  # A refused callback, or a failed on_message
)
```

**Flask**:

```python
from flask import Flask, request

app = Flask(__name__)


@app.post("/webhooks/calisero")
def calisero_webhook():
    result = handler.handle(request.get_data(), method=request.method, token=request.args.get("token"))

    return result.body, result.status, result.headers
```

**Django**:

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def calisero_webhook(request):
    result = handler.handle(request.body, method=request.method, token=request.GET.get("token"))

    return JsonResponse(result.body, status=result.status, headers=result.headers)
```

**FastAPI** (a blocking `on_message` runs off the event loop):

```python
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.post("/webhooks/calisero")
async def calisero_webhook(request: Request) -> JSONResponse:
    body = await request.body()
    result = await asyncio.to_thread(
        handler.handle, body, method=request.method, token=request.query_params.get("token")
    )

    return JSONResponse(result.body, status_code=result.status, headers=result.headers)
```

**Any WSGI server**: the handler is itself a WSGI application, so mount it where you like
(e.g. `gunicorn yourapp.webhooks:handler`, or under a path with werkzeug's `DispatcherMiddleware`). It reads the token
from the query string and refuses a body larger than `max_body_size` before reading it.

Then send the URL with the secret as each message's callback URL:
`callback_url=f"https://yourapp.com/webhooks/calisero?token={os.environ['CALISERO_WEBHOOK_TOKEN']}"`.

| Answer | When |
|---|---|
| `200 {"received": true}` | `on_message` handled the update |
| `400` / `413` | The payload is not a delivery status update / is larger than `max_body_size` (64 KiB) |
| `401` | `token` is set and the request lacks it (compared in constant time) |
| `405` | Not a POST |
| `500` | `on_message` raised |

Calisero does not sign its callbacks, which is why the handler checks a secret token in the URL instead. To read the
payload yourself, use `DeliveryWebhookMessage.from_json(raw_body)` or `DeliveryWebhookMessage.from_dict(parsed_body)`:
both raise an `InvalidWebhookPayloadError` for a malformed payload (and for the `[]` Calisero sends when the message
was cancelled meanwhile).

## Daily Sending Limit

Every account has its own daily sending limit: how many messages it can send in a day. A new account starts with a
default limit and keeps it until Calisero raises it on request.

- Every real message counts once, whatever its number of parts: the messages of `messages.create()` and the codes
  of `verifications.create()` alike. A scheduled message counts on the day it is created.
- Test messages (a sandbox account or a sandbox API key) never count and are never refused.
- The day ends at midnight, Romania time (Europe/Bucharest), whatever time zone you send from.

You can see the limit and what is left of it in three places:

```python
# 1. On the account
account = client.accounts.get("account-uuid-here").data
print(account.daily_limit, account.daily_remaining, account.sent_today)  # e.g. 1000, 873, 127

# 2. After every message or verification created (X-Daily-Limit / X-Daily-Remaining)
meta = client.messages.create(recipient="+40742***350", body="Hello!").response_meta
print(meta.daily_limit, meta.daily_remaining)  # e.g. 1000, 872 (after this message)

# 3. In every delivery status callback: message.daily_limit, message.daily_remaining, message.sent_today
```

Once the limit is reached, new messages and verifications are refused with a `DailyLimitExceededError` until
midnight, Romania time. Nothing is sent and nothing is billed:

```python
from calisero import DailyLimitExceededError

try:
    client.messages.create(recipient=recipient, body=body)
except DailyLimitExceededError as error:
    print(error.message)  # What happened and when the limit resets
    print(error.daily_limit)  # e.g. 1000
    print(error.daily_remaining)  # 0
    print(error.resets_at)  # e.g. 2026-10-01T00:00:00+03:00
    print(error.retry_after)  # Seconds until the reset
```

To raise the limit, contact Calisero with your account and the daily volume you expect.

## Rate Limits & Trace ID

### Request Rate Limit

Separately from the daily sending limit, each API user may make **240 requests a minute**, on every endpoint. Above
that the API answers `429` and the library raises a `RateLimitedError`:

```python
import time

from calisero import DailyLimitExceededError, RateLimitedError

try:
    client.messages.create(recipient=recipient, body=body)
except DailyLimitExceededError:
    ...  # The daily sending limit: wait until error.resets_at
except RateLimitedError as error:
    # The request rate limit: wait a few seconds and retry
    time.sleep(error.retry_after or 1)
    print(error.rate_limit_limit)  # 240
    print(error.rate_limit_remaining)  # 0
    print(error.rate_limit_reset)  # Unix timestamp when requests are accepted again
```

`DailyLimitExceededError` extends `RateLimitedError`, so catch it first. After any successful call,
`response_meta.rate_limit_remaining` tells how many requests are left in the current minute.

### Trace ID

Every API answer carries the request's trace ID. Log it: quoting it to support lets Calisero find the request at once,
and the dashboard shows everything that happened to it under **Developers → Debug**.

```python
from calisero import ApiError

# On success
print(client.messages.create(recipient=recipient, body=body).response_meta.trace_id)

# On error
try:
    client.messages.create(recipient=recipient, body=body)
except ApiError as error:
    logger.error("Calisero request %s failed: %s", error.trace_id, error.message)
```

## Error Handling

Every error the API answers with is an `ApiError`, of the subclass that matches its status:

```python
from calisero import (
    ApiError,
    DailyLimitExceededError,
    NotFoundError,
    RateLimitedError,
    ServerError,
    TransportError,
    UnauthorizedError,
    ValidationError,
)

try:
    client.messages.create(recipient="+40742***350", body="Test message")
except UnauthorizedError:
    print("Invalid or revoked API key")  # 401
except ValidationError as error:
    print(f"Validation error: {error.message}")  # 422
    for field, messages in error.validation_errors.items():
        print(f"{field}: {', '.join(messages)}")
except DailyLimitExceededError as error:
    print(f"Daily limit reached. Sending resumes at: {error.resets_at}")  # 429
except RateLimitedError as error:
    print(f"Rate limited. Retry after: {error.retry_after} seconds")  # 429
except ServerError as error:
    print(f"Server error: {error.message}")  # 5xx
except TransportError as error:
    print(f"Network error: {error.message}", error.__cause__)  # No answer
except ApiError as error:
    print(f"API error {error.status_code}: {error.message} (trace ID: {error.trace_id})")
```

Every `ApiError` carries the API's own error message (`message`, also its `str()`), the HTTP status
(`status_code`), the request's trace ID (`trace_id`; `request_id` returns the same value) and the decoded error body
(`error_details`). `CaliseroError` is the base class of every exception the library raises, `ApiError` and
`InvalidWebhookPayloadError` included.

| Exception | When |
|---|---|
| `UnauthorizedError` | `401`: invalid, revoked or missing API key, or a request from an IP the key does not allow |
| `ForbiddenError` | `403`: not allowed, e.g. deleting a message already sent, or another account's resource |
| `NotFoundError` | `404`: the resource does not exist |
| `ValidationError` | `422`: invalid request data; field errors in `validation_errors` |
| `DailyLimitExceededError` | `429`: the account reached its daily sending limit |
| `RateLimitedError` | `429`: more than 240 requests a minute |
| `ServerError` | `500`, `502`, `503`, `504` |
| `ApiError` | Any other API error, or an answer the library cannot read; base class of the above |
| `TransportError` | The request got no answer: network error or timeout (the original exception is its `__cause__`) |

Arguments that cannot be sent at all (an empty id, a page that is not a positive integer, a naive `datetime`) raise a
`TypeError` or a `ValueError` before any request is made.

### Retries

The library never retries a request on its own. The API takes no idempotency key, so a message retried after a
timeout or a server error may already have been sent: check with `messages.list()` before sending it again. The API
itself refuses (422, `duplicate_sms`) the same message to the same recipient sent again within 5 seconds.

## Advanced Configuration

### Client Options

```python
from calisero import AppInfo, SmsClient

client = SmsClient.create(
    os.environ["CALISERO_API_KEY"],
    timeout=10,  # Seconds to wait for the connection and each read (30 by default)
    base_url="https://rest.calisero.ro/api/v1",  # The default
    app_info=AppInfo("MyShop", "2.1.0"),  # Named in the User-Agent header
)

# One call with a timeout of its own
client.messages.list(timeout=5)
```

Every request goes to `https://rest.calisero.ro/api/v1` with a 30-second timeout and the headers
`Authorization: Bearer <key>`, `Accept: application/json`, `Content-Type: application/json` and the
[`User-Agent`](#user-agent) below. Redirects are not followed, so the API key never goes to another host.

### User-Agent

Every request names the library and its version, then the runtime, so Calisero can tell its requests apart and see
which version sent them:

```
User-Agent: Calisero-SMS-Python/1.0.1 (CPython 3.14.0; linux x86_64)
```

A request whose `User-Agent` starts with `Calisero-SMS-Python/` comes from this library. Give your application's name
with `app_info` and it follows, so the requests of each of your applications can be told apart too:

```python
client = SmsClient.create(os.environ["CALISERO_API_KEY"], app_info=AppInfo("MyShop", "2.1.0"))

print(client.http_client.user_agent)
# Calisero-SMS-Python/1.0.1 (CPython 3.14.0; linux x86_64) MyShop/2.1.0
```

Characters a header does not allow (spaces, diacritics…) become `-` in the name and the version.

### Through a Proxy, with Your Own TLS Settings

The `HTTPS_PROXY` and `NO_PROXY` environment variables apply by default. To set a proxy, or TLS settings such as a
certificate authority of your own:

```python
import ssl

client = SmsClient.create(
    os.environ["CALISERO_API_KEY"],
    proxy="http://proxy.internal:3128",
    ssl_context=ssl.create_default_context(cafile="/etc/ssl/certs/internal-ca.pem"),
)
```

### Custom Transport

A transport sends a request and returns the answer, whatever its status; it raises only when there is no answer.
Write your own to log the traffic, add headers, or plug in another HTTP client:

```python
import time

from calisero import HttpRequest, HttpResponse, SmsClient, UrllibTransport


class LoggingTransport:
    def __init__(self) -> None:
        self.inner = UrllibTransport(timeout=15)

    def send(self, request: HttpRequest) -> HttpResponse:
        started = time.perf_counter()
        response = self.inner.send(request)
        print(f"{request.method} {request.url} → {response.status} in {time.perf_counter() - started:.3f} s")

        return response


client = SmsClient.create(os.environ["CALISERO_API_KEY"], transport=LoggingTransport())
```

With [httpx](https://www.python-httpx.org) (connection pooling, HTTP/2):

```python
import httpx

from calisero import HttpRequest, HttpResponse, SmsClient


class HttpxTransport:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def send(self, request: HttpRequest) -> HttpResponse:
        response = self.client.request(
            request.method,
            request.url,
            headers=request.headers,
            content=request.body,
            timeout=request.timeout if request.timeout is not None else httpx.USE_CLIENT_DEFAULT,
        )

        return HttpResponse(response.status_code, response.headers.multi_items(), response.content)


client = SmsClient.create(os.environ["CALISERO_API_KEY"], transport=HttpxTransport(httpx.Client(timeout=30)))
```

With [requests](https://requests.readthedocs.io), `HttpResponse(response.status_code, response.headers.items(),
response.content)` reads the answer of `session.request(..., allow_redirects=False)`. A transport's request carries a
`repr()` that hides the API key, so it can be logged as is.

### Building the Client Yourself

`SmsClient.create()` covers the usual needs. For anything else, build the `HttpClient` yourself: its `last_response`
is the raw answer to the last request, headers included.

```python
from calisero import BearerTokenAuthProvider, HttpClient, SmsClient, UrllibTransport

http_client = HttpClient(
    BearerTokenAuthProvider(os.environ["CALISERO_API_KEY"]),  # Or your own get_token() provider
    transport=UrllibTransport(timeout=60),
    base_url="https://rest.calisero.ro/api/v1",
)

client = SmsClient(http_client)
client.accounts.get("account-uuid-here")

print(http_client.last_response.get_header_line("X-Trace-Id"))
```

### asyncio

The client is synchronous. In `asyncio` code, run its calls in a thread, where they do not block the event loop:

```python
message = (await asyncio.to_thread(client.messages.create, recipient="+40742***350", body="Hello!")).data
```

A client can be shared by several threads.

## Type Hints

The library ships its type information (`py.typed`) and passes `mypy --strict`: the calls, the models and the
exceptions are all typed. The models are frozen dataclasses:

```python
from calisero import CreateMessageResponse, Message, SmsClient

response: CreateMessageResponse = SmsClient.create(api_key).messages.create(recipient="+40742***350", body="Hello!")
message: Message = response.data
```

## Testing

```bash
uv run pytest                     # Run the tests
uv run pytest --cov               # With coverage
uv run ruff check . && uv run ruff format --check .   # Code style (Ruff)
uv run mypy                       # Types, strict
sh scripts/qa.sh                  # Everything CI runs: lint, types, tests, package smoke tests, examples
```

[TESTING.md](TESTING.md) describes the suite: unit tests, integration tests over real HTTP against a local server,
contract tests against the API's OpenAPI document, and smoke tests of the built package.

### Testing Your Implementation

Give the client a stub transport: your tests then run without the network and see every request.

```python
import json

from calisero import HttpRequest, HttpResponse, SmsClient


class StubTransport:
    def __init__(self, *answers: HttpResponse) -> None:
        self.answers = list(answers)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)

        return self.answers.pop(0)


def test_sends_the_order_confirmation() -> None:
    message = {
        "id": "9e2574e8-3615-4090-9b5a-0fc812079da8",
        "recipient": "+40742***350",
        "body": "Order #1001 confirmed!",
        "parts": 1,
        "created_at": "2025-02-06T10:18:43.000000Z",
        "status": "scheduled",
    }
    transport = StubTransport(HttpResponse(201, {}, json.dumps({"data": message})))
    client = SmsClient.create("test-key", transport=transport)

    send_order_confirmation(client, order)  # Your code

    assert json.loads(transport.requests[0].body) == {"recipient": "+40742***350", "body": "Order #1001 confirmed!"}
```

To test error handling, answer with the error the API sends, e.g.
`HttpResponse(422, {}, json.dumps({"message": "The recipient field is required.", "errors": {"recipient": ["The recipient field is required."]}}))`.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## Security

If you discover any security-related issues, please email support@calisero.ro instead of using the issue tracker.

## License

This library is open-sourced software licensed under the [MIT license](LICENSE.md).

## Support

- 📧 Email: support@calisero.ro
- 📖 Documentation: [https://docs.calisero.ro](https://docs.calisero.ro)
- 🐛 Issues: [GitHub Issues](https://github.com/calisero/calisero-pyton/issues)

## Changelog

Please see [CHANGELOG.md](CHANGELOG.md) for more information on what has changed recently.
