"""The transport: what sends a request to the API and brings back its answer."""

from __future__ import annotations

import math
import ssl
import urllib.error
import urllib.request
from email.message import Message
from typing import IO, ClassVar, Protocol

from calisero.http.request import HttpRequest
from calisero.http.response import HttpResponse


class Transport(Protocol):
    """Sends a request and returns the API's answer, whatever its status.

    It raises only when the request got no answer (network error, timeout): the client
    turns that into a `TransportError`. The default transport is `UrllibTransport`; a
    stub transport lets tests run without the network, and a few lines plug in another
    HTTP library (requests, httpx).
    """

    def send(self, request: HttpRequest) -> HttpResponse: ...


class UrllibTransport:
    """The default transport: urllib, from the standard library, no dependency.

    Redirects are not followed (a 3xx answer is an error, and the API key never goes to
    another host). Proxies are read from the environment (HTTPS_PROXY, NO_PROXY), unless
    `proxy` is given.
    """

    #: Seconds to wait by default.
    DEFAULT_TIMEOUT: ClassVar[float] = 30.0

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        proxy: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        """Configure the transport.

        Args:
            timeout: seconds to wait for the connection, and for each read of the answer
            proxy: the proxy every request goes through, e.g. http://proxy.internal:3128
            ssl_context: the TLS settings, e.g. a context trusting your own certificate authority

        Raises:
            TypeError: when the timeout is not a number
            ValueError: when the timeout is not a positive, finite number
        """
        #: Seconds to wait for the connection, and for each read of the answer.
        self.timeout: float = check_timeout(timeout)

        handlers: list[urllib.request.BaseHandler] = [_NoRedirectHandler()]

        if proxy is not None:
            handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))

        if ssl_context is not None:
            handlers.append(urllib.request.HTTPSHandler(context=ssl_context))

        self._opener = urllib.request.build_opener(*handlers)

    def send(self, request: HttpRequest) -> HttpResponse:
        timeout = request.timeout if request.timeout is not None else self.timeout
        data = request.body.encode("utf-8") if request.body is not None else None
        urllib_request = urllib.request.Request(  # noqa: S310 - the client sends only http(s) URLs
            request.url, data=data, headers=dict(request.headers), method=request.method
        )

        try:
            with self._opener.open(urllib_request, timeout=timeout) as response:
                return HttpResponse(response.status, response.headers.items(), response.read())
        except urllib.error.HTTPError as error:
            # urllib raises the answers with an error status (3xx included, since redirects are
            # not followed): they are answers all the same, which the client maps to errors
            with error:
                headers = error.headers.items() if error.headers is not None else ()

                return HttpResponse(error.code, headers, error.read())
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise TimeoutError(f"Request timed out after {timeout:g} s") from error

            raise ConnectionError(str(error.reason)) from error
        except TimeoutError as error:
            raise TimeoutError(f"Request timed out after {timeout:g} s") from error


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuses every redirect: the 3xx answer reaches the client as it came."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> urllib.request.Request | None:
        return None


def check_timeout(timeout: object) -> float:
    """A timeout in seconds, refused unless it is a positive, finite number.

    Raises:
        TypeError: when it is not a number
        ValueError: when it is zero, negative, infinite or NaN
    """
    message = f"The timeout must be a positive number of seconds, got {timeout!r}."

    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise TypeError(message)

    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(message)

    return float(timeout)
