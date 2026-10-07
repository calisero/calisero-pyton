"""Authentication: the API key every request carries as a bearer token."""

from __future__ import annotations

from typing import Protocol


class AuthProvider(Protocol):
    """Provides the bearer token the API authenticates requests with: the API key.

    `get_token()` is called before every request, e.g. to read the key from a secret
    manager and rotate it without a restart.
    """

    def get_token(self) -> str: ...


class BearerTokenAuthProvider:
    """Authenticates with a fixed API key."""

    __slots__ = ("_token",)

    def __init__(self, token: str) -> None:
        """Keep the API key, without the whitespace around it (a key read from a file ends with a newline).

        Raises:
            TypeError: when the key is not a string (e.g. None, for a missing environment variable)
            ValueError: when the key is empty, or holds characters an HTTP header cannot carry
        """
        self._token = check_token(token, "The API key")

    def get_token(self) -> str:
        return self._token

    def __repr__(self) -> str:
        # The key never shows up in a log or a traceback
        return "BearerTokenAuthProvider(token='***')"


def check_token(token: object, name: str) -> str:
    """The token as the Authorization header carries it: without surrounding whitespace.

    Refused when it is not a non-empty string of visible ASCII characters: the HTTP
    layer would otherwise refuse the header with an error message holding the key.

    Raises:
        TypeError: when the token is not a string
        ValueError: when it is empty or holds other characters
    """
    if not isinstance(token, str):
        raise TypeError(f"{name} must be a non-empty string.")

    token = token.strip()

    if token == "":
        raise ValueError(f"{name} must be a non-empty string.")

    if not all("!" <= character <= "~" for character in token):
        raise ValueError(f"{name} must hold only visible ASCII characters.")

    return token
