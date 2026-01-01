"""Utility modules for Mototli.

This package provides utility functions for the Mototli Gopher
client and server.
"""

from .downloads import extract_filename, get_download_dir, open_file, save_binary
from .mime import (
    get_item_type,
    get_item_type_from_mime,
    get_item_type_from_selector,
    get_mime_type,
)

__all__ = [
    "extract_filename",
    "get_download_dir",
    "get_item_type",
    "get_item_type_from_mime",
    "get_item_type_from_selector",
    "get_mime_type",
    "open_file",
    "save_binary",
]
