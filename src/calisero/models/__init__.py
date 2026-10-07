"""The resources the API answers with, as immutable dataclasses."""

from calisero.models.account import Account
from calisero.models.message import Message
from calisero.models.opt_out import OptOut
from calisero.models.pagination import ItemReader, Paginated, PaginationLinks, PaginationMeta
from calisero.models.response import ApiResponse, ResponseMeta
from calisero.models.shortened_link import ShortenedLink
from calisero.models.statuses import AccountStatus, DeliveryStatus, MessageStatus, VerificationStatus
from calisero.models.verification import Verification

__all__ = [
    "Account",
    "AccountStatus",
    "ApiResponse",
    "DeliveryStatus",
    "ItemReader",
    "Message",
    "MessageStatus",
    "OptOut",
    "Paginated",
    "PaginationLinks",
    "PaginationMeta",
    "ResponseMeta",
    "ShortenedLink",
    "Verification",
    "VerificationStatus",
]
