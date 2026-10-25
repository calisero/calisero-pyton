from __future__ import annotations

from typing import TypeAlias

from calisero._payloads import create_verification_payload, verification_check_payload
from calisero.http.client import HttpClient
from calisero.models.pagination import Paginated
from calisero.models.response import ApiResponse
from calisero.models.verification import Verification
from calisero.services._support import page_query, path_id, read_page, read_single

CreateVerificationResponse: TypeAlias = ApiResponse[Verification]
GetVerificationResponse: TypeAlias = ApiResponse[Verification]
PaginatedVerifications: TypeAlias = Paginated[Verification]


class VerificationService:
    """Verifies phone numbers with one-time codes (OTP, 2FA).

    Every call takes an optional `timeout`: seconds to wait for its answer, instead of
    the client's.
    """

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def list(
        self, *, page: int | None = None, status: str | None = None, timeout: float | None = None
    ) -> PaginatedVerifications:
        """List the verifications, newest first, 50 a page.

        Args:
            page: the page to read, from 1
            status: only the verifications with this status: "verified" or "unverified"
                (or a `VerificationStatus`)
            timeout: seconds to wait for the answer, instead of the client's
        """
        query = {**page_query(page), "status": str(status) if status is not None else None}
        result = self._http_client.get("/verifications", query, timeout=timeout)

        return read_page(result, Verification.from_dict)

    def create(
        self,
        *,
        phone: str,
        brand: str | None = None,
        template: str | None = None,
        expires_in: int | None = None,
        timeout: float | None = None,
    ) -> CreateVerificationResponse:
        """Start a verification: Calisero generates a code and sends it by SMS.

        The code's SMS counts towards the account's daily sending limit: its
        `response_meta` holds what is left of it.

        Args:
            phone: the phone number to verify, in international E.164 format
            brand: the brand named in the default message, at most 120 characters, without links:
                required unless a `template` is given
            template: a custom message, at most 600 characters, that must hold {code} and may hold no
                links (web addresses, domains, emails or IP addresses): the code goes out from a
                shared sender
            expires_in: how many minutes the code stays valid, 1 to 10: 5 when omitted
            timeout: seconds to wait for the answer, instead of the client's

        Raises:
            DailyLimitExceededError: once the account's daily sending limit is reached
        """
        payload = create_verification_payload(phone=phone, brand=brand, template=template, expires_in=expires_in)
        result = self._http_client.post("/verifications", payload, timeout=timeout)

        return read_single(result, Verification.from_dict, "verification")

    def get(self, verification_id: str, *, timeout: float | None = None) -> GetVerificationResponse:
        """Retrieve a verification by its id.

        Raises:
            NotFoundError: when there is no such verification
        """
        path = f"/verifications/{path_id(verification_id, 'verification id')}"
        result = self._http_client.get(path, timeout=timeout)

        return read_single(result, Verification.from_dict, "verification")

    def validate(self, *, phone: str, code: str, timeout: float | None = None) -> GetVerificationResponse:
        """Check a code against the latest verification of a phone number.

        Checking a verified code again succeeds.

        Args:
            phone: the phone number the code was sent to, in international E.164 format
            code: the 6-character code received, in any case
            timeout: seconds to wait for the answer, instead of the client's

        Raises:
            ValidationError: for a wrong, expired or exhausted code (5 attempts); its
                `validation_errors["code"]` says which
            NotFoundError: when no verification was started for the phone number
        """
        payload = verification_check_payload(phone=phone, code=code)
        result = self._http_client.put("/verifications/validate", payload, timeout=timeout)

        return read_single(result, Verification.from_dict, "verification")
