from __future__ import annotations

from dataclasses import dataclass

from calisero._internal.fields import FieldReader


@dataclass(frozen=True, slots=True, kw_only=True)
class Account:
    """A Calisero account."""

    id: str
    code: str
    name: str
    description: str | None
    fiscal_code: str | None
    registry_number: str | None
    iban: str | None
    city: str | None
    state: str | None
    country: str | None
    address: str | None
    postal_code: int | None
    email: str | None
    phone: str | None
    contact_person: str | None

    #: The account's credit balance.
    credit: float

    #: The account's status: compare it with the `AccountStatus` constants.
    status: str

    #: Whether this is a sandbox account: its messages are test messages, marked delivered at
    #: once, never sent to a phone nor billed.
    sandbox: bool

    #: How many messages the account can send in a day, midnight to midnight, Romania time;
    #: None when no daily limit applies.
    daily_limit: int | None

    #: How many messages the account can still send today; None when no daily limit applies.
    daily_remaining: int | None

    #: The real messages the account created today, Romania time: OTP codes included, test
    #: messages left out, one per message whatever its parts.
    sent_today: int

    created_at: str

    @classmethod
    def from_dict(cls, data: object, context: str = "account") -> Account:
        """Read an account as the API sends it.

        Raises:
            TypeError: when a required field is missing or malformed
        """
        read = FieldReader.of(data, context)
        sent_today = read.optional_integer("sent_today")

        return cls(
            id=read.string("id"),
            code=read.string("code"),
            name=read.string("name"),
            description=read.optional_string("description"),
            fiscal_code=read.optional_string("fiscal_code"),
            registry_number=read.optional_string("registry_number"),
            iban=read.optional_string("iban"),
            city=read.optional_string("city"),
            state=read.optional_string("state"),
            country=read.optional_string("country"),
            address=read.optional_string("address"),
            postal_code=read.optional_integer("postal_code"),
            email=read.optional_string("email"),
            phone=read.optional_string("phone"),
            contact_person=read.optional_string("contact_person"),
            credit=read.number("credit"),
            status=read.string("status"),
            sandbox=read.boolean("sandbox"),
            daily_limit=read.optional_integer("daily_limit"),
            daily_remaining=read.optional_integer("daily_remaining"),
            sent_today=sent_today if sent_today is not None else 0,
            created_at=read.string("created_at"),
        )
