# Contributing to Calisero Python

Thank you for considering contributing to the Calisero Python SMS API library! We welcome contributions from the community.

## Development Setup

You need Python 3.10 or later and [uv](https://docs.astral.sh/uv/) (the version in `.python-version` is the one CI
checks the code style and the types with).

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/calisero-pyton.git`
3. Install the development dependencies: `uv sync`
4. Create a new branch: `git checkout -b feature/your-feature-name`

`uv sync` creates `.venv` with the library installed in editable mode and the development tools pinned by `uv.lock`;
`uv run <command>` runs a command in it.

## Code Standards

This project follows strict coding standards:

- **Typed, strict**: `mypy --strict` on the sources, the tests, the examples and the scripts, checked against Python 3.10
- **Ruff** for formatting and linting: 4 spaces, double quotes, 120 characters a line
- **Full test coverage** for new features: CI fails below the `fail_under` of `pyproject.toml` (98%, branches included)
- **No runtime dependency**: the library uses only the Python standard library
- **Python 3.10 compatible**: no syntax or standard library feature newer than Python 3.10 in `src/`
- **The API's OpenAPI document** (`resources/openApi/api-v1.json`) is the reference: field names, types and status codes come from it, and the contract tests check them against it

### Running Quality Assurance

```bash
# Run every check, as CI does
sh scripts/qa.sh

# Or individually:
uv run ruff check .                     # Lint rules (Ruff)
uv run ruff format --check .            # Code style; `uv run ruff format .` fixes it
uv run mypy                             # Types, strict
uv run pytest                           # Tests
uv run pytest --cov                     # Tests with coverage, HTML report with --cov-report=html
sh scripts/smoke.sh                     # Build, check and install the wheel and the sdist, then use them
uv run python scripts/check_examples.py # The examples compile and import the public API
```

## Testing

- Write tests for all new functionality, in `tests/`
- Ensure existing tests continue to pass: CI runs them on Python 3.10, 3.11, 3.12, 3.13 and 3.14
- Use meaningful test names and assertions
- Cover both success and error scenarios
- Build fixtures from what the API really sends (`tests/support/fixtures.py`, the OpenAPI examples)

No test may reach the network: services run against a stub transport, the HTTP layer against a local server.
[TESTING.md](TESTING.md) describes the suite.

## Pull Request Process

1. Ensure all QA checks pass (`sh scripts/qa.sh`)
2. Update the README.md if needed
3. Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format
4. Create a Pull Request with:
   - Clear title and description
   - Reference to any related issues
   - Examples if applicable

## Releasing

The package is published to [PyPI](https://pypi.org/project/calisero/) as `calisero`.

1. Set the new version in `src/calisero/_version.py` (the package build reads it there, and it is sent in the
   `User-Agent` header): a test checks that it matches the latest version of CHANGELOG.md
2. Move the changes from `[Unreleased]` to the new version in CHANGELOG.md
3. Merge, then publish a GitHub release whose tag is the version (`v1.2.3` or `1.2.3`)

The `publish` job of the CI workflow runs once every check passed: it checks that the tag matches the version, builds
the sdist and the wheel and publishes them to PyPI with trusted publishing, which attaches the build's attestations to
each file, linking it to the commit and the workflow run that built it.

### Publishing Setup

Trusted publishing (OIDC) needs no token at all. Before the first version published to PyPI (1.0.1: the publish job
of 1.0.0 failed, so 1.0.0 exists only as a GitHub release):

1. On pypi.org, open Your projects → Publishing and add a pending GitHub publisher: project name `calisero`, owner
   `calisero`, repository `calisero-pyton`, workflow `ci.yml`, environment `pypi`. Each value must match exactly:
   PyPI refuses a publication from any other repository, workflow or environment
2. In the GitHub repository, create the `pypi` environment (Settings → Environments), optionally with required
   reviewers so that a person approves each publication

The first release then creates the project on PyPI. Later, the pending publisher becomes the project's trusted
publisher.

## Code Style

Ruff formats and lints the code (`pyproject.toml`). Key points:

- `from __future__ import annotations` at the top of every module
- Models are frozen dataclasses (`slots`, `kw_only`), with the API's snake_case field names
- Keyword-only arguments for everything but the ids of the resources
- Exceptions that say what is wrong and with which field
- Comments that explain why, not what

## Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for custom HTTP headers
fix: handle null values in message responses
docs: update README with new examples
test: add integration tests for opt-out service
```

## Reporting Issues

When reporting issues, please include:

- Python version
- Library version
- Minimal code example reproducing the issue
- Expected vs actual behavior
- Any error messages, with the trace ID (`error.trace_id`)

## Security

If you discover a security vulnerability, please send an email to support@calisero.ro instead of using the issue tracker.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
