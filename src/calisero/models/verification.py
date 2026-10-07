from __future__ import annotations

from dataclasses import dataclass

from calisero._internal.fields import FieldReader


@dataclass(frozen=True, slots=True, kw_only=True)
class Verification:
    """A phone verification: a one-time code sent by SMS, to be validated."""

    id: str
    phone: str

    #: The brand named in the default message; None when a template was used.
    brand: str | None

    #: The verification's status: compare it with the `VerificationStatus` constants.
    status: str

    #: The custom message template, holding {code}; None for the default message.
    template: str | None

    created_at: str
    expires_at: str
    verified_at: str | None

    #: How many times a code was checked against this verification.
    attempts: int

    expired: bool

    @classmethod
    def from_dict(cls, data: object, context: str = "verification") -> Verification:
        """Read a verification as the API sends it.

        Raises:
            TypeError: when a required field is missing or malformed
        """
        read = FieldReader.of(data, context)

        return cls(
            id=read.string("id"),
            phone=read.string("phone"),
            brand=read.optional_string("brand"),
            status=read.string("status"),
            template=read.optional_string("template"),
            created_at=read.string("created_at"),
            expires_at=read.string("expires_at"),
            verified_at=read.optional_string("verified_at"),
            attempts=read.integer("attempts"),
            expired=read.boolean("expired"),
        )
