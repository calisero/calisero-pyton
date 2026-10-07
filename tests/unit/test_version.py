from __future__ import annotations

import re
from importlib.metadata import version
from pathlib import Path

import calisero
from calisero import USER_AGENT, VERSION, SmsClient

ROOT = Path(__file__).resolve().parents[2]


def test_version_is_the_installed_package_version() -> None:
    assert version("calisero") == VERSION


def test_version_is_the_latest_version_of_the_changelog() -> None:
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE)

    assert match is not None
    assert match.group(1) == VERSION, "Set VERSION in src/calisero/_version.py to the version being released"


def test_version_is_a_semantic_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", VERSION)


def test_version_is_exposed_and_named_in_the_user_agent() -> None:
    assert calisero.__version__ == VERSION
    assert SmsClient.VERSION == VERSION
    assert f"Calisero-SMS-Python/{VERSION}" == USER_AGENT
