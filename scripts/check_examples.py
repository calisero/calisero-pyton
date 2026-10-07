"""Checks every example: it compiles, has a main() and imports only names the package exports.

Each example is imported as a module, which fails on a name the package does not
have; its main() is not run, so nothing is sent. mypy, which qa.sh and CI run on
examples/ too, checks how the examples use those names.

    uv run python scripts/check_examples.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(example: Path, index: int) -> None:
    source = example.read_text(encoding="utf-8")

    # compile() rather than py_compile: nothing is written next to the example
    compile(source, str(example), "exec")

    spec = importlib.util.spec_from_file_location(f"calisero_example_{index}", example)

    if spec is None or spec.loader is None:
        raise ImportError("cannot be loaded")

    module = importlib.util.module_from_spec(spec)

    # Registered as an import would be: dataclasses look their module up there
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    if not callable(getattr(module, "main", None)):
        raise AssertionError("has no main() function")


def main() -> int:
    examples = sorted((ROOT / "examples").rglob("*.py"))
    failures = 0

    for index, example in enumerate(examples):
        try:
            check(example, index)
        except Exception as error:
            failures += 1
            print(f"❌ {example.relative_to(ROOT)}: {type(error).__name__}: {error}", file=sys.stderr)

    if failures:
        print(f"{failures} example(s) failed the check", file=sys.stderr)

        return 1

    print(f"✅ {len(examples)} examples compile and import the public API")

    return 0


if __name__ == "__main__":
    sys.exit(main())
