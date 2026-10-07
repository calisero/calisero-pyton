"""The Calisero SMS API client."""

from __future__ import annotations

import ssl
from typing import ClassVar, Final, TypeGuard, cast

from calisero._version import VERSION
from calisero.auth import AuthProvider, BearerTokenAuthProvider
from calisero.http.client import DEFAULT_BASE_URL, HttpClient
from calisero.http.transport import Transport, UrllibTransport
from calisero.http.user_agent import AppInfo
from calisero.services.accounts import AccountService
from calisero.services.messages import MessageService
from calisero.services.opt_outs import OptOutService
from calisero.services.verifications import VerificationService


class SmsClient:
    """The Calisero SMS API client.

    ```python
    client = SmsClient.create(os.environ["CALISERO_API_KEY"])
    message = client.messages.create(recipient="+40742123456", body="Hello!").data
    ```
    """

    #: The library's version, sent in the User-Agent header.
    VERSION: ClassVar[str] = VERSION

    def __init__(self, http_client: HttpClient) -> None:
        """A client on an HTTP client you built yourself; `SmsClient.create()` builds one for you."""
        #: The HTTP client the services share; its `last_response` is the raw answer to the last request.
        self.http_client: Final = http_client

        #: Send and manage SMS messages.
        self.messages: Final = MessageService(http_client)

        #: Manage the phone numbers that opted out.
        self.opt_outs: Final = OptOutService(http_client)

        #: Read the account: credit, status and daily sending limit.
        self.accounts: Final = AccountService(http_client)

        #: Verify phone numbers with one-time codes.
        self.verifications: Final = VerificationService(http_client)

    @classmethod
    def create(
        cls,
        api_key: str | AuthProvider | None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = UrllibTransport.DEFAULT_TIMEOUT,
        proxy: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
        transport: Transport | None = None,
        app_info: AppInfo | None = None,
    ) -> SmsClient:
        """Create a client that authenticates with an API key, or with an `AuthProvider` of your own.

        Args:
            api_key: the API key, or an object whose `get_token()` gives it before every request
            base_url: the API's base URL
            timeout: seconds to wait for the connection and for each read of an answer; ignored
                when a `transport` is given
            proxy: the proxy every request goes through, e.g. http://proxy.internal:3128; by default
                the HTTPS_PROXY and NO_PROXY environment variables apply. Ignored when a `transport`
                is given
            ssl_context: the TLS settings; ignored when a `transport` is given
            transport: sends the requests instead of the default `UrllibTransport`, e.g. a stub in
                tests, or one built on requests or httpx
            app_info: your application, named in the User-Agent header after the library

        Raises:
            TypeError: when the API key is missing (None) or not a string
            ValueError: when the API key is empty, the timeout is not positive, the base URL is not
                an http(s) URL or the application has no usable name
        """
        # BearerTokenAuthProvider refuses anything but a non-empty string, None (a missing variable) included
        auth_provider = api_key if _is_auth_provider(api_key) else BearerTokenAuthProvider(cast(str, api_key))

        if transport is None:
            transport = UrllibTransport(timeout=timeout, proxy=proxy, ssl_context=ssl_context)

        return cls(HttpClient(auth_provider, transport=transport, base_url=base_url, app_info=app_info))


def _is_auth_provider(value: object) -> TypeGuard[AuthProvider]:
    return not isinstance(value, str) and callable(getattr(value, "get_token", None))
