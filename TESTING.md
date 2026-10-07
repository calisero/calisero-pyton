# Testing

The library's tests live in `tests/` and run with [pytest](https://docs.pytest.org). None of them reaches the
network: the services run against a stub transport, and the HTTP layer and the webhook handler against local HTTP
servers the tests start on `127.0.0.1`.

As of 1.0.0 the suite has **530 tests in 23 files** and covers 100% of the lines and branches of `src/`. CI fails
below the `fail_under` set in `pyproject.toml` (98%, branches included). Any warning fails a test, an unclosed socket
included (`filterwarnings = ["error"]`).

## Running the Tests

```bash
# All tests
uv run pytest

# With a coverage report: text in the terminal, HTML in coverage/html/index.html
uv run pytest --cov --cov-report=term-missing --cov-report=html

# One file, or the tests whose names match an expression
uv run pytest tests/unit/services/test_messages.py
uv run pytest -k "daily_limit"

# Lint, types, tests, the built package and the examples, as CI runs them
sh scripts/qa.sh
```

In the Docker environment of `automation/` (not committed), `make -f automation/Makefile test`, `qa` and
`test-matrix` run the same in containers.

## Supported Versions

CI runs the suite on Python 3.10, 3.11, 3.12, 3.13 and 3.14 on Linux, and on Python 3.14 on macOS and Windows. Every
version builds the package, installs the wheel and the sdist in fresh environments and uses them.

- The library code may use only what Python 3.10 offers: mypy checks it with `python_version = "3.10"`.
- On Windows, which has no time zone database, the development dependencies install `tzdata` for the tests that
  compare with it; the library itself falls back to the Romanian time rules without one.

## Test Files

### Unit Tests (`tests/unit`)

| File | Tests | Covers |
|---|---|---|
| `test_client.py` | 22 | `SmsClient.create()`: the services on one HTTP client, independent clients, the default base URL and transport, the API key (stripped, refused when missing, empty or unfit for a header, without showing it), an auth provider read before each request, the `base_url`, `app_info`, `timeout`, `proxy`, `ssl_context` and `transport` options; `SmsClient(http_client)` |
| `test_version.py` | 4 | `VERSION` matches the installed package and the latest version of CHANGELOG.md, and is named in the `User-Agent` |
| `test_errors.py` | 17 | The exception hierarchy, the attributes of each exception and their defaults, copies of the details, pickling |
| `test_payloads.py` | 25 | The request bodies: API field names in the documented order, options left out when `None`, kept when `False` or `0`; `schedule_at` in Romania time, summer and winter time and the switches between them, other time zones, naive datetimes refused; the fallback to the European rule without a time zone database, checked against the database from 1997 to 2040 |
| `test_internal.py` | 34 | Describing values for error messages, integers and numbers as JavaScript reads them, decimal strings, JSON without NaN, a decoder out of stack turned into a `ValueError`, the API key hidden from `repr()` |

#### HTTP Layer (`tests/unit/http`)

| File | Tests | Covers |
|---|---|---|
| `test_http_client.py` | 33 | The requests: method, URL, query string (booleans, encoding), headers, the User-Agent with and without your application, JSON body (UTF-8 included); base URLs refused unless http(s); per-call timeouts; the auth provider and its errors; tokens a header cannot carry; no Idempotency-Key; the answers: JSON, empty, `[]`, not JSON, NaN; `last_response` |
| `test_response_handling.py` | 43 | Every error status mapped to its exception; the message and the trace ID (header in any case, body, `X-Request-ID`); error bodies that are not JSON; 422 field errors; the request rate limit's 429 against the daily sending limit's; headers that are not whole seconds; requests that got no answer; interruptions let through |
| `test_http_response.py` | 8 | Header names matched case-insensitively; repeated headers; headers from a mapping, pairs or an HTTP library's headers; bodies as bytes |
| `test_urllib_transport.py` | 24 | Over real HTTP: the request and the answer, error statuses as answers, redirects not followed, timeouts (the transport's and the request's), refused connections, the options, proxies (given, or from the environment), TLS settings |
| `test_user_agent.py` | 12 | The User-Agent: the library and its version, then the runtime (CPython, PyPy, none), then your application, reduced to the characters a header allows so it cannot break the header |

#### Models (`tests/unit/models`)

| File | Tests | Covers |
|---|---|---|
| `test_message.py` | 17 | Messages with every field, the minimal ones, shortened links; status constants; errors naming the field at fault, nested ones included; immutability |
| `test_account.py` | 17 | Full and minimal accounts, the daily limit, credits as numbers or decimal strings, malformed credits refused |
| `test_opt_out_and_verification.py` | 9 | Opt-outs with and without a reason; verifications unverified, verified, expired, sent with a template |
| `test_pagination_and_meta.py` | 11 | Pages, empty last pages, links and meta, iteration; `ResponseMeta` read from the headers, in any case, ignoring values that are not counts |
| `test_delivery_webhook_message.py` | 22 | Callback payloads from text or bytes: full, minimal, without the daily limit, amounts as strings; refusing invalid JSON, invalid UTF-8, deep nesting (whatever the platform's stack), `[]`, and every missing or malformed required field |

#### Services (`tests/unit/services`)

Each test answers with a stub transport (`tests/support/stub_transport.py`) and checks the request the service sends
(method, URL, query, body, timeout) and what it reads from the answer, headers included.

| File | Tests | Covers |
|---|---|---|
| `test_messages.py` | 27 | `create()` with every option, scheduled, with shortened links, its `response_meta`, the daily limit and validation errors; `get()`, ids encoded, empty ids refused, unexpected answers; `list()` and its pages; `delete()` |
| `test_opt_outs.py` | 11 | `create()` with and without a reason, a duplicate; `get()`, `list()`, `update()`, `delete()`; empty ids |
| `test_verifications.py` | 12 | `list()` with the status filter; `create()` with a brand or a template, the daily limit; `get()`; `validate()` and each of its 422s, and its 404 |
| `test_accounts.py` | 5 | `get()` for a typical account, a sandbox one without a daily limit; 401 and 403 |
| `test_support.py` | 10 | The services' helpers: reading answers and pages, the page query, ids encoded as `encodeURIComponent()` does |

#### Webhooks (`tests/unit/webhooks`)

| File | Tests | Covers |
|---|---|---|
| `test_handler.py` | 43 | `handle()`: the answers (200, 400, 401, 405, 413, 500), raw and decoded bodies, sizes in bytes, the token checked in constant time, `on_error`, the options; as a WSGI application: the query string, refusals before the body is read, declared and chunked lengths; over real HTTP with `wsgiref` |

### Integration Tests (`tests/integration`)

| File | Tests | Covers |
|---|---|---|
| `test_http.py` | 12 | The library with its default urllib transport against a local server: headers (the User-Agent included) and UTF-8 bodies on the wire, answers and their headers, `[]` deletes, error mapping, HTML error pages, redirects not followed, timeouts (the client's and a call's), refused connections, 20 concurrent requests each reading its own answer, proxies |

### Contract Tests (`tests/contract`)

| File | Tests | Covers |
|---|---|---|
| `test_openapi.py` | 112 | The library against the API's OpenAPI document (`resources/openApi/api-v1.json`): every documented operation is implemented with its method, path and query; every documented example answer is read; every documented field of every resource is read; every documented request field can be sent, and nothing else; every documented error example maps to its exception class with its message |

When the API changes, replace `resources/openApi/api-v1.json` with the new document: the contract tests then show
what the library lacks.

## Package Tests (`scripts/`)

Run by `sh scripts/qa.sh` and by CI on every Python version:

- `smoke.sh` builds the sdist and the wheel, checks their contents (`check_package.py`: every module and `py.typed` in
  the wheel, the metadata, no runtime dependency, nothing of the repository's tooling) and how PyPI renders them
  (`twine check --strict`), then installs each in a fresh virtual environment and runs `smoke_test.py` there, outside
  the working copy: the public names, a message sent through a stub transport, a webhook payload read.
- `check_examples.py` compiles every example and imports it without running it, so an example cannot use a name the
  package does not export; mypy checks the rest of their use of the library.

CI also checks that the library keeps no runtime dependency, and audits the development dependencies (`pip-audit`).

## Writing Tests

- Build fixtures from what the API really sends: `tests/support/fixtures.py` and the OpenAPI examples.
- Answer with `json_response()` through a `StubTransport`, or with a local server (`tests/support/local_server.py`)
  to test what goes over the wire.
- Cover the error paths as well as the successful ones: each exception and the headers and body fields it reads.
- Run `sh scripts/qa.sh` before opening a pull request.
