"""Checks the contents of the built wheel and sdist: what users install, and nothing else.

uv run --no-project python scripts/check_package.py dist/
"""

from __future__ import annotations

import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_wheel(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as archive:
        files = archive.namelist()
        metadata_file = next(name for name in files if name.endswith(".dist-info/METADATA"))
        metadata = Parser().parsestr(archive.read(metadata_file).decode("utf-8"))

    sources = sorted(path.relative_to(ROOT / "src").as_posix() for path in (ROOT / "src" / "calisero").rglob("*.py"))
    missing = [name for name in [*sources, "calisero/py.typed"] if name not in files]
    unexpected = [name for name in files if name.split("/")[0] in ("tests", "examples", "scripts", "resources")]
    errors = [f"wheel: missing {name}" for name in missing] + [f"wheel: unexpected {name}" for name in unexpected]

    expected_metadata = {"Name": "calisero", "License-Expression": "MIT", "Requires-Python": ">=3.10"}

    for field, value in expected_metadata.items():
        if metadata.get(field) != value:
            errors.append(f"wheel: {field} is {metadata.get(field)!r}, not {value!r}")

    # The library has no runtime dependency, and must keep none
    errors += [f"wheel: runtime dependency {requirement}" for requirement in metadata.get_all("Requires-Dist") or []]

    print(f"{wheel.name}: {len(files)} files, {metadata['Name']} {metadata['Version']}")

    return errors


def check_sdist(sdist: Path) -> list[str]:
    with tarfile.open(sdist) as archive:
        files = [name.split("/", 1)[1] for name in archive.getnames() if "/" in name]

    required = [
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "LICENSE.md",
        "src/calisero/__init__.py",
        "src/calisero/py.typed",
        "tests/contract/test_openapi.py",
        "resources/openApi/api-v1.json",
    ]
    errors = [f"sdist: missing {name}" for name in required if name not in files]
    errors += [
        f"sdist: unexpected {name}"
        for name in files
        if name.split("/")[0] in ("automation", ".github", "examples", "scripts", "coverage", "dist")
    ]

    print(f"{sdist.name}: {len(files)} files")

    return errors


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    wheels, sdists = sorted(dist.glob("*.whl")), sorted(dist.glob("*.tar.gz"))

    if len(wheels) != 1 or len(sdists) != 1:
        print(f"Expected one wheel and one sdist in {dist}, found {len(wheels)} and {len(sdists)}", file=sys.stderr)

        return 1

    errors = check_wheel(wheels[0]) + check_sdist(sdists[0])

    for error in errors:
        print(f"❌ {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
