"""The HTTP layer: the client that talks to the API, and the transport that carries its requests."""

from calisero.http.client import DEFAULT_BASE_URL, HttpClient, HttpResult, QueryValue
from calisero.http.request import HttpMethod, HttpRequest
from calisero.http.response import HttpResponse, ResponseHeaders
from calisero.http.transport import Transport, UrllibTransport
from calisero.http.user_agent import USER_AGENT, AppInfo, RuntimeInfo, build_user_agent

__all__ = [
    "DEFAULT_BASE_URL",
    "USER_AGENT",
    "AppInfo",
    "HttpClient",
    "HttpMethod",
    "HttpRequest",
    "HttpResponse",
    "HttpResult",
    "QueryValue",
    "ResponseHeaders",
    "RuntimeInfo",
    "Transport",
    "UrllibTransport",
    "build_user_agent",
]
