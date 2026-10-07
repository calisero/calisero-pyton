# Changelog

All notable changes to `calisero` (the Calisero Python library) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-06

First release of the official Python library for the Calisero SMS API, covering version 1.0.14 of the API: the same API surface as `calisero/calisero-php` 2.3.1 and `@calisero/calisero-node` 1.0.1, with a synchronous, fully typed Python interface.

### Added
- **`SmsClient`** with `SmsClient.create(api_key, ...)`: `base_url`, `timeout` (30 s by default), `proxy`, `ssl_context`, `app_info`, or a `transport` of your own. `SmsClient(http_client)` builds the client on an `HttpClient` you configured yourself.
- **Messages** (`client.messages`): `create()`, `get()`, `list(page=...)` and `delete()`. `create()` accepts every option of the API as keyword arguments, `schedule_at` included as a timezone-aware `datetime`, converted to the `YYYY-MM-DD HH:MM:SS` Romania time the API expects (summer and winter time handled, with or without a time zone database on the system).
- **URL shortening**: `shorten_urls=True` and `Message.shortened_urls`, each `ShortenedLink` with its click statistics.
- **Opt-outs** (`client.opt_outs`): `create()`, `get()`, `list(page=...)`, `update()` and `delete()`.
- **Verifications (OTP)** (`client.verifications`): `create()`, `get()`, `list(page=..., status=...)` and `validate()`.
- **Accounts** (`client.accounts`): `get()`, with the credit, the status and the daily sending limit (`daily_limit`, `daily_remaining`, `sent_today`).
- **Response metadata**: every response carries a `ResponseMeta` (`response_meta`) read from the answer's headers: the trace ID, the request rate limit and, for a created message or verification, what is left of the daily sending limit.
- **Models**: immutable dataclasses (`Message`, `ShortenedLink`, `OptOut`, `Verification`, `Account`, `Paginated`, `PaginationLinks`, `PaginationMeta`), with the API's own snake_case field names; a page iterates over its items. Statuses stay the strings the API sends, and the `MessageStatus`, `VerificationStatus`, `AccountStatus` and `DeliveryStatus` string enums give the known values to compare them with.
- **Errors**: `ApiError` and its subclasses `UnauthorizedError` (401), `ForbiddenError` (403), `NotFoundError` (404), `ValidationError` (422, with `validation_errors`), `RateLimitedError` (429, request rate limit), `DailyLimitExceededError` (429, daily sending limit, extends `RateLimitedError`), `ServerError` (5xx) and `TransportError` (no answer: network error, timeout). Each carries the API's message, the HTTP status, the trace ID and the decoded error body; `CaliseroError` is the base of everything the library raises.
- **Delivery status webhooks**: `DeliveryWebhookMessage.from_json()` and `from_dict()` read and validate the callback payload, and `DeliveryWebhookHandler` answers the callbacks from a view of any web framework (`handle()`) or as a WSGI application, with an optional secret `token` checked in constant time.
- **User-Agent**: every request names the library, its version and the runtime, e.g. `Calisero-SMS-Python/1.0.0 (CPython 3.14.0; linux x86_64)`, so the platform can tell its requests apart. `app_info=AppInfo("MyShop", "2.1.0")` appends your application; `client.http_client.user_agent` shows the header sent.
- **Timeouts per call**: every call takes a `timeout` keyword, overriding the client's for that call.
- **Zero runtime dependencies**: the HTTP layer is `urllib`, from the standard library. A transport built on requests or httpx takes a few lines.
- **Typed**: the package ships its type information (`py.typed`) and passes `mypy --strict`.
- Examples for every operation in `examples/`.
- Tests: unit tests, integration tests against a local HTTP server (proxies, redirects, timeouts and concurrent requests included), contract tests against the API's OpenAPI document, webhook handler tests over real HTTP, and a smoke test of the built wheel and sdist. CI runs them on Python 3.10 to 3.14, on Linux, macOS and Windows.

### Notes
- The library sends no `Idempotency-Key` header and never retries a request: the API takes no idempotency key, so a create retried after a timeout or a server error could send the message twice. The API refuses (422, `duplicate_sms`) the same message to the same recipient sent again within 5 seconds.
- The client is synchronous. In `asyncio` code, run its calls in a thread with `asyncio.to_thread()`.
