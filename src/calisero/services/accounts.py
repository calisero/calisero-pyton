from __future__ import annotations

from typing import TypeAlias

from calisero.http.client import HttpClient
from calisero.models.account import Account
from calisero.models.response import ApiResponse
from calisero.services._support import path_id, read_single

GetAccountResponse: TypeAlias = ApiResponse[Account]


class AccountService:
    """Reads the account: credit, status and daily sending limit."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def get(self, account_id: str, *, timeout: float | None = None) -> GetAccountResponse:
        """Retrieve an account by its id.

        Args:
            account_id: the account's id, shown in the dashboard
            timeout: seconds to wait for the answer, instead of the client's

        Raises:
            NotFoundError: when there is no such account
            ForbiddenError: when the account is not the API key's
        """
        result = self._http_client.get(f"/accounts/{path_id(account_id, 'account id')}", timeout=timeout)

        return read_single(result, Account.from_dict, "account")
