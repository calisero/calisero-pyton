"""Official Python library for the Calisero SMS API.

```python
import os

from calisero import SmsClient

client = SmsClient.create(os.environ["CALISERO_API_KEY"])
message = client.messages.create(recipient="+40742123456", body="Hello from Calisero!").data
```
"""

from calisero._version import VERSION
from calisero.auth import AuthProvider, BearerTokenAuthProvider
from calisero.client import SmsClient
from calisero.errors import (
    ApiError,
    CaliseroError,
    DailyLimitExceededError,
    ForbiddenError,
    InvalidWebhookPayloadError,
    NotFoundError,
    RateLimitedError,
    ServerError,
    TransportError,
    UnauthorizedError,
    ValidationError,
)
from calisero.http import (
    DEFAULT_BASE_URL,
    USER_AGENT,
    AppInfo,
    HttpClient,
    HttpMethod,
    HttpRequest,
    HttpResponse,
    HttpResult,
    QueryValue,
    ResponseHeaders,
    Transport,
    UrllibTransport,
)
from calisero.models import (
    Account,
    AccountStatus,
    ApiResponse,
    DeliveryStatus,
    Message,
    MessageStatus,
    OptOut,
    Paginated,
    PaginationLinks,
    PaginationMeta,
    ResponseMeta,
    ShortenedLink,
    Verification,
    VerificationStatus,
)
from calisero.services import (
    AccountService,
    CreateMessageResponse,
    CreateOptOutResponse,
    CreateVerificationResponse,
    GetAccountResponse,
    GetMessageResponse,
    GetOptOutResponse,
    GetVerificationResponse,
    MessageService,
    OptOutService,
    PaginatedMessages,
    PaginatedOptOuts,
    PaginatedVerifications,
    VerificationService,
)
from calisero.webhooks import DeliveryWebhookHandler, DeliveryWebhookMessage, WebhookResponse

__version__ = VERSION

__all__ = [
    "DEFAULT_BASE_URL",
    "USER_AGENT",
    "VERSION",
    "Account",
    "AccountService",
    "AccountStatus",
    "ApiError",
    "ApiResponse",
    "AppInfo",
    "AuthProvider",
    "BearerTokenAuthProvider",
    "CaliseroError",
    "CreateMessageResponse",
    "CreateOptOutResponse",
    "CreateVerificationResponse",
    "DailyLimitExceededError",
    "DeliveryStatus",
    "DeliveryWebhookHandler",
    "DeliveryWebhookMessage",
    "ForbiddenError",
    "GetAccountResponse",
    "GetMessageResponse",
    "GetOptOutResponse",
    "GetVerificationResponse",
    "HttpClient",
    "HttpMethod",
    "HttpRequest",
    "HttpResponse",
    "HttpResult",
    "InvalidWebhookPayloadError",
    "Message",
    "MessageService",
    "MessageStatus",
    "NotFoundError",
    "OptOut",
    "OptOutService",
    "Paginated",
    "PaginatedMessages",
    "PaginatedOptOuts",
    "PaginatedVerifications",
    "PaginationLinks",
    "PaginationMeta",
    "QueryValue",
    "RateLimitedError",
    "ResponseHeaders",
    "ResponseMeta",
    "ServerError",
    "ShortenedLink",
    "SmsClient",
    "Transport",
    "TransportError",
    "UnauthorizedError",
    "UrllibTransport",
    "ValidationError",
    "Verification",
    "VerificationService",
    "VerificationStatus",
    "WebhookResponse",
    "__version__",
]
