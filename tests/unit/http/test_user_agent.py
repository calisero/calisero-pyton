from __future__ import annotations

import platform
import sys

import pytest

from calisero import USER_AGENT, VERSION, AppInfo
from calisero.http.user_agent import RuntimeInfo, build_user_agent

CPYTHON = RuntimeInfo("CPython", "3.14.0", "linux", "x86_64")
LIBRARY = f"Calisero-SMS-Python/{VERSION}"


def test_opens_with_the_library_and_its_version() -> None:
    assert USER_AGENT == LIBRARY
    assert build_user_agent().startswith(f"{LIBRARY} (")


def test_names_the_python_the_operating_system_and_the_processor_of_this_process() -> None:
    assert build_user_agent() == (
        f"{LIBRARY} ({platform.python_implementation()} {platform.python_version()}; "
        f"{sys.platform} {platform.machine()})"
    )


def test_names_the_runtime_it_is_given() -> None:
    assert build_user_agent(None, CPYTHON) == f"{LIBRARY} (CPython 3.14.0; linux x86_64)"
    assert build_user_agent(None, RuntimeInfo("PyPy", "3.11.13", "darwin", "arm64")) == (
        f"{LIBRARY} (PyPy 3.11.13; darwin arm64)"
    )
    assert build_user_agent(None, RuntimeInfo("CPython", "3.10.18", "win32", "")) == (
        f"{LIBRARY} (CPython 3.10.18; win32)"
    )
    assert build_user_agent(None, RuntimeInfo("CPython", "3.12.11", "", "")) == f"{LIBRARY} (CPython 3.12.11)"


def test_names_only_the_library_without_a_runtime_to_describe() -> None:
    assert build_user_agent(None, None) == USER_AGENT
    assert build_user_agent(None, RuntimeInfo("", "", "linux", "x86_64")) == USER_AGENT


def test_names_your_application_after_the_library() -> None:
    assert build_user_agent(AppInfo("MyShop", "2.1.0"), CPYTHON) == (
        f"{LIBRARY} (CPython 3.14.0; linux x86_64) MyShop/2.1.0"
    )
    assert build_user_agent(AppInfo("MyShop"), CPYTHON) == f"{LIBRARY} (CPython 3.14.0; linux x86_64) MyShop"
    assert build_user_agent(AppInfo("MyShop", ""), CPYTHON) == f"{LIBRARY} (CPython 3.14.0; linux x86_64) MyShop"


def test_keeps_the_header_a_single_valid_line_whatever_the_application_name() -> None:
    assert build_user_agent(AppInfo("My Shop\r\nX-Injected: yes", "2.1 (beta)"), CPYTHON) == (
        f"{LIBRARY} (CPython 3.14.0; linux x86_64) My-Shop-X-Injected-yes/2.1-beta"
    )
    assert build_user_agent(AppInfo("Magazinul Ștefan", "1.0"), CPYTHON) == (
        f"{LIBRARY} (CPython 3.14.0; linux x86_64) Magazinul-tefan/1.0"
    )


def test_keeps_the_runtime_comment_valid_whatever_the_platform_reports() -> None:
    assert build_user_agent(None, RuntimeInfo("CPython", "3.14.0", "linux (custom)", "x86 64")) == (
        f"{LIBRARY} (CPython 3.14.0; linux-custom x86-64)"
    )


@pytest.mark.parametrize("name", ["", "   ", "()"])
def test_refuses_an_application_name_without_a_usable_character(name: str) -> None:
    with pytest.raises(ValueError, match=r"^app_info\.name must name your application with letters, digits"):
        build_user_agent(AppInfo(name), CPYTHON)


def test_refuses_an_application_name_that_is_not_text() -> None:
    with pytest.raises(TypeError, match=r"^app_info\.name must name your application"):
        build_user_agent(AppInfo(42), CPYTHON)  # type: ignore[arg-type]


def test_describes_the_runtime_of_this_process() -> None:
    runtime = RuntimeInfo.current()

    assert runtime == RuntimeInfo(
        platform.python_implementation(), platform.python_version(), sys.platform, platform.machine()
    )
