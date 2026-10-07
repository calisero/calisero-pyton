from __future__ import annotations

import pytest

from calisero import DailyLimitExceededError, NotFoundError, ValidationError, VerificationStatus
from tests.support.fixtures import DAILY_LIMIT_BODY, PHONE, VERIFICATION_ID, page_of, verification_data
from tests.support.stub_transport import client_answering, json_response, request_body

BASE = "https://rest.calisero.ro/api/v1"


class TestList:
    def test_lists_the_verifications(self) -> None:
        client, transport = client_answering(json_response(200, page_of([verification_data()], "verifications")))

        page = client.verifications.list()

        assert transport.last_request.url == f"{BASE}/verifications"
        assert [verification.id for verification in page] == [VERIFICATION_ID]

    def test_filters_by_status_on_any_page(self) -> None:
        client, transport = client_answering(
            json_response(200, page_of([], "verifications", 2)),
            json_response(200, page_of([], "verifications")),
        )

        client.verifications.list(page=2, status="verified")
        client.verifications.list(status=VerificationStatus.UNVERIFIED)

        assert [request.url for request in transport.requests] == [
            f"{BASE}/verifications?page=2&status=verified",
            f"{BASE}/verifications?status=unverified",
        ]


class TestCreate:
    def test_starts_a_verification_with_a_brand(self) -> None:
        headers = {"X-Daily-Limit": "1000", "X-Daily-Remaining": "871"}
        client, transport = client_answering(json_response(201, {"data": verification_data()}, headers))

        response = client.verifications.create(phone=PHONE, brand="Calisero")

        assert (transport.last_request.method, transport.last_request.url) == ("POST", f"{BASE}/verifications")
        assert request_body(transport.last_request) == {"phone": PHONE, "brand": "Calisero"}
        assert response.data.status == VerificationStatus.UNVERIFIED
        assert (response.response_meta.daily_limit, response.response_meta.daily_remaining) == (1000, 871)

    def test_starts_a_verification_with_a_template_and_an_expiry(self) -> None:
        data = verification_data(brand=None, template="Your code: {code}")
        client, transport = client_answering(json_response(201, {"data": data}))

        response = client.verifications.create(phone=PHONE, template="Your code: {code}", expires_in=10)

        assert request_body(transport.last_request) == {
            "phone": PHONE,
            "template": "Your code: {code}",
            "expires_in": 10,
        }
        assert response.data.template == "Your code: {code}"

    def test_raises_the_daily_limit_refusal(self) -> None:
        client, _ = client_answering(json_response(429, DAILY_LIMIT_BODY))

        with pytest.raises(DailyLimitExceededError):
            client.verifications.create(phone=PHONE, brand="Calisero")


def test_get_retrieves_a_verification() -> None:
    client, transport = client_answering(json_response(200, {"data": verification_data()}))

    response = client.verifications.get(VERIFICATION_ID)

    assert transport.last_request.url == f"{BASE}/verifications/{VERIFICATION_ID}"
    assert response.data.id == VERIFICATION_ID


def test_get_refuses_an_empty_id() -> None:
    client, _ = client_answering()

    with pytest.raises(ValueError, match=r"^The verification id must be a non-empty string\.$"):
        client.verifications.get("")


class TestValidate:
    def test_checks_a_code(self) -> None:
        data = verification_data(status="verified", verified_at="2025-11-08T10:10:02.000000Z", attempts=1)
        client, transport = client_answering(json_response(200, {"data": data}))

        response = client.verifications.validate(phone=PHONE, code="ABC123")

        assert (transport.last_request.method, transport.last_request.url) == (
            "PUT",
            f"{BASE}/verifications/validate",
        )
        assert request_body(transport.last_request) == {"phone": PHONE, "code": "ABC123"}
        assert response.data.status == VerificationStatus.VERIFIED

    @pytest.mark.parametrize(
        "message",
        [
            "The verification code is invalid.",
            "The verification code has expired.",
            "Too many attempts. Please request a new code.",
        ],
    )
    def test_raises_a_validation_error_for_a_code_refused(self, message: str) -> None:
        client, _ = client_answering(json_response(422, {"message": message, "errors": {"code": [message]}}))

        with pytest.raises(ValidationError) as caught:
            client.verifications.validate(phone=PHONE, code="WRONG1")

        assert caught.value.validation_errors == {"code": [message]}

    def test_raises_not_found_without_a_verification_for_the_phone(self) -> None:
        client, _ = client_answering(json_response(404, {"message": "Resource not found!"}))

        with pytest.raises(NotFoundError):
            client.verifications.validate(phone=PHONE, code="ABC123")
