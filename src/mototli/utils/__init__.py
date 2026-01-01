"""Utility modules for Mototli.

This package provides utility functions for the Mototli Gopher
client and server.
"""

from .mime import get_item_type, get_item_type_from_mime, get_mime_type

__all__ = [
    "get_mime_type",
    "get_item_type",
    "get_item_type_from_mime",
]
