from __future__ import annotations

from dataclasses import dataclass

from calisero._internal.fields import FieldReader


@dataclass(frozen=True, slots=True, kw_only=True)
class OptOut:
    """A phone number that opted out of receiving messages."""

    id: str
    phone: str
    reason: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: object, context: str = "opt-out") -> OptOut:
        """Read an opt-out as the API sends it.

        Raises:
            TypeError: when a required field is missing or malformed
        """
        read = FieldReader.of(data, context)

        return cls(
            id=read.string("id"),
            phone=read.string("phone"),
            reason=read.optional_string("reason"),
            created_at=read.string("created_at"),
            updated_at=read.string("updated_at"),
        )
