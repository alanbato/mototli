"""Gopher protocol definitions and abstractions."""

from mototli.protocol.attributes import GopherAttributes, ViewInfo
from mototli.protocol.constants import CRLF, DEFAULT_PORT, GOPHER_TERMINATOR
from mototli.protocol.item_types import ItemType
from mototli.protocol.request import GopherRequest, RequestType
from mototli.protocol.response import GopherItem, GopherResponse

__all__ = [
    "CRLF",
    "DEFAULT_PORT",
    "GOPHER_TERMINATOR",
    "GopherAttributes",
    "GopherItem",
    "GopherRequest",
    "GopherResponse",
    "ItemType",
    "RequestType",
    "ViewInfo",
]
