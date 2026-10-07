from __future__ import annotations

import pytest

from calisero import AccountStatus, ForbiddenError, UnauthorizedError
from tests.support.fixtures import ACCOUNT_ID, account_data
from tests.support.stub_transport import client_answering, json_response

BASE = "https://rest.calisero.ro/api/v1"


def test_get_retrieves_an_account() -> None:
    client, transport = client_answering(json_response(200, {"data": account_data()}))

    account = client.accounts.get(ACCOUNT_ID).data

    assert (transport.last_request.method, transport.last_request.url) == ("GET", f"{BASE}/accounts/{ACCOUNT_ID}")
    assert (account.name, account.credit, account.status) == ("My Company", 100.5, AccountStatus.ACTIVE)
    assert (account.daily_limit, account.daily_remaining, account.sent_today) == (1000, 873, 127)


def test_get_reads_a_sandbox_account_without_a_daily_limit() -> None:
    data = account_data(sandbox=True, daily_limit=None, daily_remaining=None, sent_today=0)
    client, _ = client_answering(json_response(200, {"data": data}))

    account = client.accounts.get(ACCOUNT_ID).data

    assert (account.sandbox, account.daily_limit, account.daily_remaining) == (True, None, None)


def test_get_raises_unauthorized_for_an_invalid_key() -> None:
    client, _ = client_answering(json_response(401, {"message": "Unauthenticated."}))

    with pytest.raises(UnauthorizedError, match=r"^Unauthenticated\.$"):
        client.accounts.get(ACCOUNT_ID)


def test_get_raises_forbidden_for_another_account() -> None:
    client, _ = client_answering(json_response(403, {"message": "This action is unauthorized."}))

    with pytest.raises(ForbiddenError):
        client.accounts.get(ACCOUNT_ID)


def test_get_refuses_an_id_that_is_not_text() -> None:
    client, _ = client_answering()

    with pytest.raises(TypeError, match=r"^The account id must be a non-empty string\.$"):
        client.accounts.get(42)  # type: ignore[arg-type]
