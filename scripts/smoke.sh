#!/bin/sh
# Builds the sdist and the wheel (the wheel from the sdist, as uv build does), checks what
# they hold and how PyPI will render them, then installs each in a fresh virtual environment
# of its own and runs scripts/smoke_test.py with it: the package as users get it, without
# the sources.
#
#   sh scripts/smoke.sh
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

uv build --quiet --out-dir "$work/dist" "$root"
uv run --no-project --quiet python "$root/scripts/check_package.py" "$work/dist"
uvx --quiet twine check --strict "$work"/dist/*

for artifact in "$work"/dist/*.whl "$work"/dist/*.tar.gz; do
    rm -rf "$work/venv"
    uv venv --quiet "$work/venv"
    uv pip install --quiet --python "$work/venv/bin/python" "$artifact"

    printf '%s: ' "$(basename "$artifact")"
    # From outside the working copy, so that nothing but the installed package can be imported
    (cd "$work" && "$work/venv/bin/python" "$root/scripts/smoke_test.py")
done
