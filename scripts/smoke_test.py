"""Uses the package as it is installed from the wheel or the sdist, without the sources.

scripts/smoke.sh runs it in a fresh virtual environment where only the built package
is installed: it checks the public names, the type information and a message sent
through a stub transport.
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

import calisero
from calisero import HttpRequest, HttpResponse

EXPECTED_EXPORTS = [
    "SmsClient",
    "VERSION",
    "HttpClient",
    "UrllibTransport",
    "HttpRequest",
    "HttpResponse",
    "BearerTokenAuthProvider",
    "AppInfo",
    "MessageService",
    "OptOutService",
    "AccountService",
    "VerificationService",
    "Message",
    "ShortenedLink",
    "OptOut",
    "Account",
    "Verification",
    "Paginated",
    "ResponseMeta",
    "ApiResponse",
    "MessageStatus",
    "VerificationStatus",
    "AccountStatus",
    "DeliveryStatus",
    "DeliveryWebhookMessage",
    "DeliveryWebhookHandler",
    "CaliseroError",
    "ApiError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationError",
    "RateLimitedError",
    "DailyLimitExceededError",
    "ServerError",
    "TransportError",
    "InvalidWebhookPayloadError",
]

MESSAGE: dict[str, Any] = {
    "id": "9e2574e8-3615-4090-9b5a-0fc812079da8",
    "recipient": "+40742123456",
    "body": "Smoke test",
    "parts": 1,
    "created_at": "2026-10-06T10:00:00.000000Z",
    "status": "scheduled",
}

RUNTIME = f"({platform.python_implementation()} {platform.python_version()}; {sys.platform} {platform.machine()})"


class SmokeTransport:
    def send(self, request: HttpRequest) -> HttpResponse:
        assert request.headers["User-Agent"] == f"Calisero-SMS-Python/{calisero.VERSION} {RUNTIME}"
        assert request.headers["Authorization"] == "Bearer smoke-test-key"

        return HttpResponse(201, {"X-Trace-Id": "smoke"}, json.dumps({"data": MESSAGE}))


def main() -> None:
    package = Path(calisero.__file__).resolve().parent

    # Installed, with its type information, and not imported from the working copy
    assert "site-packages" in package.parts, f"calisero was imported from {package}"
    assert (package / "py.typed").is_file(), "py.typed is missing"

    missing = [name for name in EXPECTED_EXPORTS if not hasattr(calisero, name)]
    assert not missing, f"the package does not export {missing}"
    assert set(EXPECTED_EXPORTS) <= set(calisero.__all__)

    client = calisero.SmsClient.create("smoke-test-key", transport=SmokeTransport())
    response = client.messages.create(recipient=MESSAGE["recipient"], body="Smoke test")

    assert isinstance(response.data, calisero.Message)
    assert response.data.id == MESSAGE["id"]
    assert response.response_meta.trace_id == "smoke"
    assert issubclass(calisero.DailyLimitExceededError, calisero.RateLimitedError)

    message = calisero.DeliveryWebhookMessage.from_json(
        '{"messageId":"019961db-14a7-7348-963f-5a7a789a969f","recipient":"+40742123456","status":"delivered",'
        '"price":0.0378}'
    )
    assert message.status == calisero.DeliveryStatus.DELIVERED

    print(f"✅ calisero {calisero.__version__} works, installed in {package.parent} ({RUNTIME[1:-1]})")


if __name__ == "__main__":
    main()
