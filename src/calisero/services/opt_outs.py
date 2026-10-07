from __future__ import annotations

from typing import TypeAlias

from calisero._payloads import opt_out_payload
from calisero.http.client import HttpClient
from calisero.models.opt_out import OptOut
from calisero.models.pagination import Paginated
from calisero.models.response import ApiResponse
from calisero.services._support import page_query, path_id, read_page, read_single

CreateOptOutResponse: TypeAlias = ApiResponse[OptOut]
GetOptOutResponse: TypeAlias = ApiResponse[OptOut]
PaginatedOptOuts: TypeAlias = Paginated[OptOut]


class OptOutService:
    """Manages the phone numbers that opted out of receiving messages.

    The API refuses to send to an opted-out number. Every call takes an optional
    `timeout`: seconds to wait for its answer, instead of the client's.
    """

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def create(self, *, phone: str, reason: str | None = None, timeout: float | None = None) -> CreateOptOutResponse:
        """Opt a phone number out.

        Args:
            phone: the phone number in international E.164 format
            reason: why the number opted out, at most 600 characters
            timeout: seconds to wait for the answer, instead of the client's

        Raises:
            ValidationError: e.g. when the number already opted out
        """
        result = self._http_client.post("/opt-outs", opt_out_payload(phone=phone, reason=reason), timeout=timeout)

        return read_single(result, OptOut.from_dict, "opt-out")

    def get(self, opt_out_id: str, *, timeout: float | None = None) -> GetOptOutResponse:
        """Retrieve an opt-out by its id.

        Raises:
            NotFoundError: when there is no such opt-out
        """
        result = self._http_client.get(f"/opt-outs/{path_id(opt_out_id, 'opt-out id')}", timeout=timeout)

        return read_single(result, OptOut.from_dict, "opt-out")

    def list(self, *, page: int | None = None, timeout: float | None = None) -> PaginatedOptOuts:
        """List the opt-outs, 50 a page.

        Args:
            page: the page to read, from 1
            timeout: seconds to wait for the answer, instead of the client's
        """
        result = self._http_client.get("/opt-outs", page_query(page), timeout=timeout)

        return read_page(result, OptOut.from_dict)

    def update(
        self, opt_out_id: str, *, phone: str, reason: str | None = None, timeout: float | None = None
    ) -> GetOptOutResponse:
        """Update an opt-out.

        Args:
            opt_out_id: the opt-out's id
            phone: the phone number in international E.164 format
            reason: why the number opted out, at most 600 characters
            timeout: seconds to wait for the answer, instead of the client's
        """
        path = f"/opt-outs/{path_id(opt_out_id, 'opt-out id')}"
        result = self._http_client.put(path, opt_out_payload(phone=phone, reason=reason), timeout=timeout)

        return read_single(result, OptOut.from_dict, "opt-out")

    def delete(self, opt_out_id: str, *, timeout: float | None = None) -> None:
        """Delete an opt-out: the number can receive messages again."""
        self._http_client.delete(f"/opt-outs/{path_id(opt_out_id, 'opt-out id')}", timeout=timeout)
