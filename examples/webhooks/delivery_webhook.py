"""Receive delivery status callbacks.

Calisero posts a JSON payload to a message's callback URL each time its status
changes (sent, delivered or undelivered). Answer with any 2xx status within
2 seconds: only a failed connection or a slower answer is retried, at most
5 attempts in total; a non-2xx answer is not retried.

Calisero does not sign its callbacks: add a secret token to the callback URL you
send (https://yourapp.com/webhooks/calisero?token=...) and set it here as
CALISERO_WEBHOOK_TOKEN, so that only your callback URLs are accepted.

    CALISERO_WEBHOOK_TOKEN=s3cr3t python examples/webhooks/delivery_webhook.py

    curl -X POST 'http://localhost:8080/webhooks/calisero?token=s3cr3t' -H 'Content-Type: application/json' \
         -d '{"messageId": "019961db-14a7-7348-963f-5a7a789a969f", "recipient": "+40742***350",
              "status": "delivered", "price": 0.0378}'
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import TYPE_CHECKING
from wsgiref.simple_server import make_server

from calisero import DeliveryStatus, DeliveryWebhookHandler, DeliveryWebhookMessage

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment

PATH = "/webhooks/calisero"


def on_message(message: DeliveryWebhookMessage) -> None:
    """Keep the work here short (update a record, queue a job): the answer waits for it."""
    if message.status == DeliveryStatus.DELIVERED:
        line = f"📬 Message {message.message_id} delivered to {message.recipient} at {message.delivered_at}"
    elif message.status == DeliveryStatus.UNDELIVERED:
        line = f"❌ Message {message.message_id} could not be delivered to {message.recipient}"
    else:
        line = f"📤 Message {message.message_id} sent to {message.recipient} at {message.sent_at}"

    line += f" | price: {message.price:.4f} | balance: {message.remaining_balance or 'N/A'}"

    # The account's daily sending limit as it stood when the callback was sent
    if message.daily_limit is not None:
        line += f" | daily limit: {message.daily_remaining} of {message.daily_limit} messages left today"

    print(line, flush=True)


def on_error(error: Exception) -> None:
    """A refused callback (bad token, malformed payload) or a failed on_message."""
    print(f"⚠️ {error}", flush=True)


handler = DeliveryWebhookHandler(
    on_message,
    token=os.environ.get("CALISERO_WEBHOOK_TOKEN") or None,
    on_error=on_error,
)


def app(environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
    """The handler is a WSGI application: here it answers at PATH only."""
    if environ.get("PATH_INFO") == PATH:
        return handler(environ, start_response)

    start_response("404 Not Found", [("Content-Type", "text/plain")])

    return [b"Not found"]


def main() -> None:
    # 127.0.0.1 by default; HOST=0.0.0.0 inside a container, to reach it from the host
    host = os.environ.get("HOST") or "127.0.0.1"
    port = int(os.environ.get("PORT") or 8080)

    with make_server(host, port, app) as server:
        print(f"👂 Listening for delivery status callbacks on http://localhost:{port}{PATH}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
