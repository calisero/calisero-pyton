"""The User-Agent header: the library, its version, the runtime and, when given, your application."""

from __future__ import annotations

import platform
import re
import sys
from dataclasses import dataclass
from typing import Final

from calisero._version import VERSION

#: The product token that opens the User-Agent header of every request: the library and its
#: version. A request whose User-Agent starts with `Calisero-SMS-Python/` comes from this library.
USER_AGENT: Final = f"Calisero-SMS-Python/{VERSION}"

# What an HTTP header token may hold (RFC 9110): anything else becomes "-"
_NOT_TOKEN: Final = re.compile(r"[^A-Za-z0-9!#$%&'*+.^_`|~-]+")


@dataclass(frozen=True, slots=True)
class AppInfo:
    """Your application, named in the User-Agent header after the library."""

    #: Your application's name, e.g. MyShop.
    name: str

    #: Your application's version, e.g. 2.1.0.
    version: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeInfo:
    """What the User-Agent header says of the runtime."""

    #: The Python implementation, e.g. CPython or PyPy.
    implementation: str

    #: The version of Python, e.g. 3.14.0.
    version: str

    #: The operating system, as sys.platform names it: linux, darwin, win32...
    system: str

    #: The processor, e.g. x86_64 or arm64.
    machine: str

    @classmethod
    def current(cls) -> RuntimeInfo:
        """The runtime of this process."""
        return cls(platform.python_implementation(), platform.python_version(), sys.platform, platform.machine())


#: The runtime of this process.
RUNTIME: Final = RuntimeInfo.current()


def build_user_agent(app_info: AppInfo | None = None, runtime: RuntimeInfo | None = RUNTIME) -> str:
    """The User-Agent header: the library and its version, the runtime and, when given, your application.

    For example `Calisero-SMS-Python/1.0.0 (CPython 3.14.0; linux x86_64) MyShop/2.1.0`.

    Args:
        app_info: your application, named after the library
        runtime: the runtime to describe: this process by default, None for none

    Raises:
        TypeError: when the application's name is not a string
        ValueError: when the application's name has no usable character
    """
    parts = [USER_AGENT]
    comment = _runtime_comment(runtime)

    if comment is not None:
        parts.append(comment)

    if app_info is not None:
        parts.append(_app_product(app_info))

    return " ".join(parts)


def _runtime_comment(runtime: RuntimeInfo | None) -> str | None:
    """The runtime, its version, the operating system and the processor, e.g. `(CPython 3.14.0; linux x86_64)`."""
    if runtime is None:
        return None

    name = " ".join(part for part in (_to_token(runtime.implementation), _to_token(runtime.version)) if part)

    if name == "":
        return None

    system = " ".join(part for part in (_to_token(runtime.system), _to_token(runtime.machine)) if part)

    return f"({name}; {system})" if system else f"({name})"


def _app_product(app_info: AppInfo) -> str:
    """The application as a product token, `name/version`, so the header stays a single valid line."""
    message = "app_info.name must name your application with letters, digits or -._ characters."

    if not isinstance(app_info.name, str):
        raise TypeError(message)

    name = _to_token(app_info.name)
    version = _to_token(app_info.version) if isinstance(app_info.version, str) else ""

    if name == "":
        raise ValueError(message)

    return f"{name}/{version}" if version else name


def _to_token(value: str) -> str:
    return _NOT_TOKEN.sub("-", value).strip("-")
