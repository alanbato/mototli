"""Gopher item types.

This module defines the item types used in Gopher protocol responses
as specified in RFC 1436 and common extensions.
"""

from enum import Enum


class ItemType(str, Enum):
    """Gopher item types.

    Each item in a Gopher directory has a single-character type that indicates
    what kind of resource it represents. The canonical types are defined in
    RFC 1436, with additional types added by common extensions.
    """

    # RFC 1436 canonical types
    TEXT = "0"
    """Text file (item is a file that may be displayed)."""

    DIRECTORY = "1"
    """Gopher directory (item leads to another menu)."""

    CSO = "2"
    """CSO phone-book server (item refers to a name server)."""

    ERROR = "3"
    """Error (item is an error message)."""

    BINHEX = "4"
    """BinHexed Macintosh file."""

    DOS_BINARY = "5"
    """DOS binary archive (e.g., .zip files)."""

    UUENCODED = "6"
    """UNIX uuencoded file."""

    SEARCH = "7"
    """Index-Search server (item refers to a search engine)."""

    TELNET = "8"
    """Text-based Telnet session."""

    BINARY = "9"
    """Binary file (client must read until connection closes)."""

    MIRROR = "+"
    """Redundant server / mirror."""

    GIF = "g"
    """GIF image."""

    IMAGE = "I"
    """Image file (other than GIF)."""

    TN3270 = "T"
    """Text-based TN3270 session."""

    # Common extensions (Gopher+)
    HTML = "h"
    """HTML file (commonly used for web links)."""

    INFO = "i"
    """Informational message (not selectable)."""

    AUDIO = "s"
    """Sound/audio file."""

    DOC = "d"
    """Document (word processor format)."""

    PNG = "p"
    """PNG image."""

    # Gopher+ specific
    BITMAP = ":"
    """Bitmap image (Gopher+)."""

    MOVIE = ";"
    """Movie file (Gopher+)."""

    @classmethod
    def from_char(cls, char: str) -> "ItemType":
        """Get ItemType from a single character.

        Args:
            char: Single character representing the item type.

        Returns:
            The corresponding ItemType.

        Raises:
            ValueError: If the character is not a known item type.
        """
        for item_type in cls:
            if item_type.value == char:
                return item_type
        raise ValueError(f"Unknown item type: {char!r}")

    @property
    def is_directory(self) -> bool:
        """Check if this item type represents a directory listing."""
        return self == ItemType.DIRECTORY

    @property
    def is_search(self) -> bool:
        """Check if this item type represents a search service."""
        return self == ItemType.SEARCH

    @property
    def is_binary(self) -> bool:
        """Check if this item type represents binary content."""
        return self in {
            ItemType.BINARY,
            ItemType.DOS_BINARY,
            ItemType.BINHEX,
            ItemType.UUENCODED,
            ItemType.GIF,
            ItemType.IMAGE,
            ItemType.PNG,
            ItemType.BITMAP,
            ItemType.MOVIE,
            ItemType.AUDIO,
        }

    @property
    def is_text(self) -> bool:
        """Check if this item type represents text content."""
        return self in {
            ItemType.TEXT,
            ItemType.HTML,
            ItemType.DOC,
        }

    @property
    def is_informational(self) -> bool:
        """Check if this item type is informational (not selectable)."""
        return self in {ItemType.INFO, ItemType.ERROR}

    @property
    def is_external(self) -> bool:
        """Check if this item type refers to an external session."""
        return self in {ItemType.TELNET, ItemType.TN3270}
