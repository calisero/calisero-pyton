from __future__ import annotations

import pytest

from calisero import Account, AccountStatus
from tests.support.fixtures import ACCOUNT_ID, account_data, without


def test_reads_an_account_with_every_field() -> None:
    assert Account.from_dict(account_data()) == Account(
        id=ACCOUNT_ID,
        code="ABC1234",
        name="My Company",
        description="Company description",
        fiscal_code="RO12345678",
        registry_number="J40/123456/2023",
        iban="RO49AAAA1B31007593840000",
        city="Bucharest",
        state="Bucharest",
        country="RO",
        address="Main Street 123",
        postal_code=123456,
        email="contact@company.com",
        phone="+40721***456",
        contact_person="John Doe",
        credit=100.5,
        status="active",
        sandbox=False,
        daily_limit=1000,
        daily_remaining=873,
        sent_today=127,
        created_at="2024-09-20T12:48:55.000000Z",
    )


def test_reads_an_account_without_its_optional_details() -> None:
    optional = (
        "description",
        "fiscal_code",
        "registry_number",
        "iban",
        "city",
        "state",
        "country",
        "address",
        "email",
        "phone",
        "contact_person",
    )
    account = Account.from_dict(account_data(postal_code=None, **dict.fromkeys(optional)))

    assert all(getattr(account, name) is None for name in optional)
    assert account.postal_code is None


def test_reads_an_account_without_a_daily_limit() -> None:
    account = Account.from_dict(account_data(daily_limit=None, daily_remaining=None, sandbox=True))

    assert (account.daily_limit, account.daily_remaining, account.sandbox) == (None, None, True)


def test_reads_an_account_that_predates_the_daily_limit() -> None:
    account = Account.from_dict(without(account_data(), "daily_limit", "daily_remaining", "sent_today"))

    assert (account.daily_limit, account.daily_remaining, account.sent_today) == (None, None, 0)


@pytest.mark.parametrize(("credit", "expected"), [(100, 100.0), ("100.50", 100.5), (" 12.5 ", 12.5), ("1e3", 1000.0)])
def test_reads_the_credit_as_a_number_or_a_decimal_string(credit: object, expected: float) -> None:
    assert Account.from_dict(account_data(credit=credit)).credit == expected


@pytest.mark.parametrize("credit", ["free", "", "inf", "nan", "1_000", True, None])
def test_refuses_a_credit_that_is_not_a_number(credit: object) -> None:
    with pytest.raises(TypeError, match=r'^Invalid account: "credit" must be a number, got '):
        Account.from_dict(account_data(credit=credit))


def test_refuses_a_sandbox_flag_that_is_not_a_boolean() -> None:
    with pytest.raises(TypeError, match=r'^Invalid account: "sandbox" must be a boolean, got a number\.$'):
        Account.from_dict(account_data(sandbox=0))


def test_compares_the_status_with_the_constants() -> None:
    assert Account.from_dict(account_data()).status == AccountStatus.ACTIVE
    assert Account.from_dict(account_data(status="disabled")).status == AccountStatus.DISABLED
