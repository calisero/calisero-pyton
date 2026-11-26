# Changelog

All notable changes to `calisero` (the Calisero Python library) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-11-26

Support for versions 1.0.16 and 1.0.17 of the Calisero API, 1.0.17 as documented on 18.11.2026 (approved link domains included). Their changes are all on the API's side: no field or endpoint was added, so the library's code and API are unchanged; only the version in the `User-Agent` header moves to 1.0.2. Upgrading needs no code change, but two of them change what an application sees: a verification code validates only once, and an account restricted to its approved link domains may link only to them.

### Changed
- `examples/messages/send_advanced_sms.py` reads the sender ID from `CALISERO_SENDER`, and sends under the default sender without it. It used `Calisero`, which the API documents as a placeholder: a sender that is not approved for the account is refused with a 422, and nothing is sent. It also says its link must go to one of your approved link domains.
- `examples/verifications/validate_verification.py` no longer says a code may be validated again.

### Documentation
- **Approved link domains** (API 1.0.17, 18.11.2026). On an account restricted to its approved link domains, every link in a message's body, with or without `https://`, must go to a domain approved for the account, test messages included; links Calisero shortens are checked by the address they open. `messages.create()` raises any other link as a `ValidationError` on `validation_errors["body"]`, its message naming the refused domain: the message is not created, not sent and not billed. A scheduled message whose domain is rejected or revoked before it is due is not sent: its status becomes `failed` (error code 1005 in the dashboard). A new "Approved Link Domains" section of `README.md`, with how to tell a refused link from a refused sender, `AGENTS.md` and the docstring of `messages.create()` say so.
- **A code validates only once** (API 1.0.17). `verifications.validate()` with a code that already verified is refused with a `ValidationError` ("The validation code has already been used.") instead of succeeding again. `README.md`, `AGENTS.md` and the docstring of `verifications.validate()`, which said checking a verified code again succeeds, now say so.
- **TLS** (API 1.0.16): the API accepts TLS 1.2 and TLS 1.3 only since 1 November 2026, refusing a client that offers only TLS 1.0 or 1.1 during the handshake, and redirects `http://` to `https://`. Python 3.10 and later offer TLS 1.2 and 1.3 by default, so the library needs no change; a new "TLS" section of `README.md`, and `AGENTS.md`, say why the base URL must stay `https://` and what an `ssl_context` of your own must allow.
- **Senders**: a sender that is unknown, still pending, rejected or another account's is refused with a `ValidationError` ("The sender is invalid or is not approved." on `sender`), in `README.md`, `AGENTS.md` and the docstring of `messages.create()`.
- **URL shortening**: test messages (a sandbox account or API key) keep their links as written and come back with an empty `shortened_urls`, in `README.md`, `AGENTS.md` and the docstring of `messages.create()`.
- `examples/README.md`: the `CALISERO_SENDER` variable.

### Tests
- The contract tests follow version 1.0.17 of the API's OpenAPI document (`resources/openApi/api-v1.json`, as of 18.11.2026): its own validation error answer for `POST /messages`, with a refused sender and a refused link domain as examples, and the refusal of a code already used by `PUT /verifications/validate`, each read as a `ValidationError` with the API's message.
- Unit tests for the refusal of a sender not approved, of a link to a domain not approved and of a code already used, and a test that the default TLS settings offer TLS 1.2 or later.
- `pyproject.toml`: uv rebuilds the editable install when `src/calisero/_version.py` changes (`[tool.uv] cache-keys`), so the test that matches the installed version against it passes right after a version bump, without `uv sync --reinstall`.

## [1.0.1] - 2026-10-25

The first version published to PyPI: the publish job of 1.0.0 failed, so 1.0.0 exists only as a GitHub release. The library's code and API are unchanged; only the version in the `User-Agent` header moves to 1.0.1.

### Changed
- Checked against version 1.0.15 of the Calisero API. Its OpenAPI document (`resources/openApi/api-v1.json`) now describes the delivery status webhook as a callback of `POST /messages`, and documents the rules of `callback_url` (a public http or https address), `sender` (approved for the account, written exactly as approved) and of a verification's `brand` and `template` (no links). The API's operations and fields are unchanged, and so is the library; the contract tests read the new document.

### Fixed
- The project URLs of the package metadata (`pyproject.toml`), the README's badges, `git clone` command and issues link, and the `git clone` command of `CONTRIBUTING.md` named `calisero/calisero-python` instead of the library's repository, `calisero/calisero-pyton`.

### Documentation
- `AGENTS.md`: guidance for AI coding agents, both for integrating Calisero into an application with this library (configuration, sending, OTP, statuses, the delivery webhook, errors and trace IDs, sandbox keys, the pitfalls of the API) and for working on the library. It ships in the sdist, which `scripts/check_package.py` now checks.
- `README.md` and the docstrings of `messages.create()` and `verifications.create()`: the rules API 1.0.15 documents for `callback_url`, `sender`, and a verification's `brand` and `template`.
- `CONTRIBUTING.md`: the "Publishing Setup" section names the repository the PyPI trusted publisher is configured for, `calisero-pyton`.

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
