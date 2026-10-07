from __future__ import annotations

import pytest

from calisero import OptOut, Verification, VerificationStatus
from tests.support.fixtures import OPT_OUT_ID, PHONE, VERIFICATION_ID, opt_out_data, verification_data


class TestOptOut:
    def test_reads_an_opt_out_with_a_reason(self) -> None:
        assert OptOut.from_dict(opt_out_data()) == OptOut(
            id=OPT_OUT_ID,
            phone=PHONE,
            reason="Customer asked to stop receiving messages",
            created_at="2025-09-19T12:01:15.000000Z",
            updated_at="2025-09-19T12:01:15.000000Z",
        )

    def test_reads_an_opt_out_without_a_reason(self) -> None:
        assert OptOut.from_dict(opt_out_data(reason=None)).reason is None

    def test_refuses_an_opt_out_without_a_phone(self) -> None:
        with pytest.raises(TypeError, match=r'^Invalid opt-out: "phone" must be a string, got null\.$'):
            OptOut.from_dict(opt_out_data(phone=None))


class TestVerification:
    def test_reads_an_unverified_verification(self) -> None:
        assert Verification.from_dict(verification_data()) == Verification(
            id=VERIFICATION_ID,
            phone=PHONE,
            brand="Calisero",
            status="unverified",
            template=None,
            created_at="2025-11-08T10:09:38.000000Z",
            expires_at="2025-11-08T10:12:38.000000Z",
            verified_at=None,
            attempts=0,
            expired=False,
        )

    def test_reads_a_verified_verification(self) -> None:
        verification = Verification.from_dict(
            verification_data(status="verified", verified_at="2025-11-08T10:10:02.000000Z", attempts=1)
        )

        assert verification.status == VerificationStatus.VERIFIED
        assert (verification.verified_at, verification.attempts) == ("2025-11-08T10:10:02.000000Z", 1)

    def test_reads_an_expired_verification(self) -> None:
        verification = Verification.from_dict(verification_data(expired=True, attempts=5))

        assert verification.status == VerificationStatus.UNVERIFIED
        assert (verification.expired, verification.attempts) == (True, 5)

    def test_reads_a_verification_sent_with_a_template(self) -> None:
        verification = Verification.from_dict(verification_data(brand=None, template="Your code: {code}"))

        assert (verification.brand, verification.template) == (None, "Your code: {code}")

    def test_refuses_attempts_that_are_not_a_count(self) -> None:
        with pytest.raises(TypeError, match=r'^Invalid verification: "attempts" must be an integer, got a string\.$'):
            Verification.from_dict(verification_data(attempts="1"))

    def test_status_constants_are_their_values(self) -> None:
        assert str(VerificationStatus.VERIFIED) == "verified"
        assert f"{VerificationStatus.UNVERIFIED}" == "unverified"
        assert VerificationStatus("verified") is VerificationStatus.VERIFIED
