# AGENTS.md: calisero (Python)

Guidance for AI coding agents. Calisero is a Romanian transactional SMS API (base URL
`https://rest.calisero.ro/api/v1`, `Authorization: Bearer <API key>`). `calisero` is its official Python library:
fully typed (`py.typed`), no runtime dependency (the HTTP client is `urllib`), synchronous, Python 3.10 or later.

- **Using this library**: you are adding Calisero to an application.
- **Working on this library**: you are changing this repository.

Every name below exists in `src/calisero/` (exported from `calisero/__init__.py`); `README.md` documents each call in
full.

## Using this library

### Install and configure

Install it from PyPI:

```bash
pip install calisero  # or: uv add calisero, poetry add calisero
```

The library reads no environment variable for the key: pass it to `SmsClient.create()`. By convention the
application reads it from `CALISERO_API_KEY`. Never hard-code the key, never ship it to a browser or a mobile app, use
one key per environment.

```python
import os

from calisero import SmsClient

client = SmsClient.create(os.environ["CALISERO_API_KEY"])  # None raises TypeError, "" raises ValueError
```

Create the client once and share it. Keyword options: `timeout` (seconds), `base_url`, `proxy`, `ssl_context`,
`transport`, `app_info`. Instead of the key you may pass an object with a `get_token()` method, called before every
request. Every call takes a `timeout=` of its own too.

### Send an SMS

```python
response = client.messages.create(
    recipient="+40712345678",  # E.164
    body="Your order #1001 has shipped.",  # at most 1600 characters
    # sender="MyShop",  # only a sender approved for the account
    # schedule_at=datetime.now(timezone.utc) + timedelta(hours=1),  # timezone-aware, converted to Romania time
    # callback_url=f"https://example.com/webhooks/calisero?token={os.environ['CALISERO_WEBHOOK_TOKEN']}",
    # shorten_urls=True, visible_body="...", validity=24 (hours)
)
message = response.data

print(message.id, message.status, message.parts, response.response_meta.trace_id)
```

Keep `message.id`: it matches the delivery callbacks. `response.response_meta.daily_remaining` (`None` without a
daily limit) says how many messages the account can still send today.

### OTP: send and validate

Calisero generates the code (6 characters, letters and digits, case-insensitive), sends it and checks it: never
generate or store it yourself.

```python
from calisero import ValidationError, VerificationStatus

client.verifications.create(phone="+40712345678", brand="MyShop")
# or template="Your MyShop code is {code}"; expires_in: 1 to 10 minutes (5 by default)

try:
    verification = client.verifications.validate(phone=phone, code=user_input).data
    verified = verification.status == VerificationStatus.VERIFIED
except ValidationError as error:
    ...  # wrong or expired code, or too many attempts (422): error.message says which
```

### Read a message's status

```python
from calisero import MessageStatus

message = client.messages.get(message_id).data
if message.status == MessageStatus.DELIVERED:
    ...  # message.sent_at, message.delivered_at
```

`client.messages.list(page=2)` lists messages (50 a page); `client.messages.delete(message_id)` cancels a message
that is still scheduled. A message that stays `sent` was not confirmed by the carrier, which does not mean it failed.

### Delivery webhook

Set `callback_url` on the message, then use `DeliveryWebhookHandler`:

```python
from calisero import DeliveryWebhookHandler, DeliveryWebhookMessage


def on_message(message: DeliveryWebhookMessage) -> None:
    # message.message_id, message.status ("sent", "delivered", "undelivered"), message.delivered_at,
    # message.price, message.remaining_balance, message.daily_remaining
    deliveries.enqueue(message.message_id, message.status)  # store or enqueue, then return


handler = DeliveryWebhookHandler(on_message, token=os.environ["CALISERO_WEBHOOK_TOKEN"], on_error=print)


# Flask; Django and FastAPI work the same way (see README.md), and the handler is itself a WSGI app
@app.post("/webhooks/calisero")
def calisero_webhook():
    result = handler.handle(request.get_data(), method=request.method, token=request.args.get("token"))
    return result.body, result.status, result.headers
```

The answer is given once `on_message` returns, and Calisero waits 2 seconds: keep it fast. If `on_message` raises,
the answer is `500`, which Calisero does not retry: persist first, process later. To parse a body yourself, use
`DeliveryWebhookMessage.from_json(raw)` or `DeliveryWebhookMessage.from_dict(data)` (an
`InvalidWebhookPayloadError` for a malformed one). With Django, exempt the view from CSRF (`@csrf_exempt`).

### Errors and the trace ID

Every API error is an `ApiError` (`message`, `status_code`, `trace_id`, `error_details`), of the subclass of its
status; all library exceptions derive from `CaliseroError`.

| Exception | When |
| --- | --- |
| `UnauthorizedError` | 401: missing, invalid or revoked API key |
| `ForbiddenError` | 403: not allowed, e.g. deleting a message that is no longer scheduled |
| `NotFoundError` | 404: unknown ID |
| `ValidationError` | 422: `validation_errors` maps each field to its messages |
| `DailyLimitExceededError` | 429 with `daily_limit_exceeded` (`daily_limit`, `resets_at`); subclass of `RateLimitedError`, so catch it first |
| `RateLimitedError` | 429: request rate limit, wait `retry_after` seconds |
| `ServerError` | 500, 502, 503, 504 |
| `TransportError` | no answer: network error or timeout |

Log `error.trace_id` with every failure and `response.response_meta.trace_id` with every success. Every answer carries
it as `X-Trace-Id` (an error body also as `trace_id`); the dashboard's Developers → Debug page shows everything that
happened to that request.

### Tests

- Unit tests: pass `transport=` a stub whose `send(request)` returns `HttpResponse(status, headers, body)` (see
  "Testing Your Implementation" in `README.md`).
- Staging and CI against the real API: use a sandbox API key. It goes through the same validation but sends nothing,
  bills nothing and never counts towards the daily limit; the message is `delivered` at once, callbacks still arrive,
  and a test OTP code shows in the dashboard.

### Rules that matter

- **Phone numbers** in E.164: `+40712345678`, not `0712345678`. Normalise user input before sending.
- **Length and cost**: one part holds 160 GSM-7 characters, or 70 when the text has Romanian diacritics (ă, â, î, ș,
  ț) or emoji (UCS-2). A longer text is split into parts, each billed as one SMS (`parts` on the message); `body`
  takes at most 1600 characters. When cost matters, a text without diacritics keeps 160-character parts: an option,
  not a rule.
- **Sender ID**: alphanumeric, at most 11 characters, approved for the account and written exactly as approved;
  otherwise 422 and nothing is sent. Omit `sender` for the default sender. It cannot receive replies. Never take it
  from user input. OTP codes go out from the shared "Verify" sender and need no sender of your own.
- **Scheduling**: the API reads `schedule_at` as `YYYY-MM-DD HH:MM:SS`, Romania time (Europe/Bucharest). Pass a
  timezone-aware `datetime` and the library converts it (a naive one raises `ValueError`); a string is sent as is and
  must already be in that format and time zone.
- **Webhooks**: answer any 2xx within 2 seconds, do the work afterwards. Only a timeout or a failed connection is
  retried (at most 5 attempts); a non-2xx answer is not. The same update can arrive twice and out of order: key your
  processing on `message_id` + `status`, and never move a message back from `delivered`. `callback_url` must be a
  public http(s) URL: private, loopback and link-local addresses are refused.
- **429 has two meanings**: the request rate limit (240 requests a minute; retry after `retry_after`) and the daily
  sending limit (`DailyLimitExceededError`: nothing sent, retrying the same day will not help; it resets at midnight,
  Romania time, `resets_at`). Created messages and verifications report `X-Daily-Limit` / `X-Daily-Remaining` in
  `response_meta`.
- **No idempotency key**: the library never retries, and you should not retry `messages.create()` blindly after a
  timeout or a `TransportError`: the SMS may have been sent and billed. Check `messages.list()` first. Do not put sends
  under a task queue's automatic retries (Celery `autoretry_for` and the like).
- **OTP**: `brand` or a `template` holding `{code}`, neither with links. Each code is a billed SMS that counts towards
  the daily limit: rate-limit resends in your application.

## Working on this library

Read `CONTRIBUTING.md` (standards, release) and `TESTING.md` (the suite) before changing code.

- **Layout**: `src/calisero/client.py` (entry point), `services/` (one per resource), `models/` (frozen dataclasses
  with the API's field names), `errors.py`, `http/` (transport, headers, User-Agent), `webhooks/`, `_internal/` (Romania
  time, JSON reading). Tests in `tests/` (`unit`, `integration`, `contract`, `support`), runnable examples in
  `examples/`, QA and packaging scripts in `scripts/`.
- **OpenAPI**: `resources/openApi/api-v1.json` is the API's contract. Field names, types and status codes come from
  it, and `tests/contract/test_openapi.py` checks the library against it.
- **Checks** (with [uv](https://docs.astral.sh/uv/)):

  ```bash
  uv sync
  sh scripts/qa.sh                                 # everything CI runs, in order
  uv run ruff check . && uv run ruff format --check .
  uv run mypy                                      # strict, on src, tests, examples and scripts
  uv run pytest --cov                              # fails below 98% coverage; warnings are errors
  ```

  If a local `automation/` folder exists (it is not committed), its Makefile runs the same in Docker.
- **Conventions**: Python 3.10 compatible in `src/`, standard library only, `mypy --strict` clean, Ruff style (120
  columns, double quotes). No test may reach the network: services run on a stub transport, the HTTP layer on a local
  server. Build fixtures from what the API really sends.
- **Package contents**: `[tool.hatch.build.targets.sdist]` in `pyproject.toml` lists what the sdist ships (`AGENTS.md`
  included); `scripts/check_package.py` checks the built wheel and sdist.
- **Changelog and version**: note changes under `[Unreleased]` in `CHANGELOG.md`; a release sets `VERSION` in
  `src/calisero/_version.py`, which a test matches against the latest changelog version.
