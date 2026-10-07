#!/bin/sh
# Every check CI runs, in its order: the code style, the types, the tests with coverage, the
# built package and the examples. Run it from anywhere, with uv installed:
#
#   sh scripts/qa.sh
set -eu

cd "$(dirname "$0")/.."

uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov --cov-report=term-missing --cov-report=html --cov-report=xml
sh scripts/smoke.sh
uv run python scripts/check_examples.py
