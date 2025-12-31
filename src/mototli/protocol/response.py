"""Gopher protocol response representation.

This module provides dataclasses for representing Gopher protocol responses,
including directory listings and individual items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .constants import CRLF, DEFAULT_PORT, GOPHER_TERMINATOR, TAB
from .item_types import ItemType

if TYPE_CHECKING:
    from .attributes import GopherAttributes


@dataclass(frozen=True)
class GopherItem:
    """Represents a single item in a Gopher directory listing.

    Each line in a Gopher directory follows this format:
    TYPE DISPLAY_TEXT TAB SELECTOR TAB HOSTNAME TAB PORT CRLF

    Where TYPE is a single character indicating the item type.

    Attributes:
        item_type: The type of this item (text, directory, etc.).
        display_text: Human-readable text shown to the user.
        selector: Path/selector to request this item.
        hostname: Server hostname where this item is located.
        port: Server port (default 70).
        gopher_plus: Whether this server supports Gopher+.

    Examples:
        >>> item = GopherItem(
        ...     item_type=ItemType.TEXT,
        ...     display_text="About this server",
        ...     selector="/about",
        ...     hostname="example.com",
        ... )
        >>> item.to_line()
        b'0About this server\\t/about\\texample.com\\t70\\r\\n'
    """

    item_type: ItemType
    display_text: str
    selector: str
    hostname: str
    port: int = DEFAULT_PORT
    gopher_plus: bool = False

    @classmethod
    def from_line(cls, line: bytes) -> GopherItem:
        """Parse a Gopher item from a directory listing line.

        Args:
            line: A single line from a Gopher directory listing.

        Returns:
            A GopherItem instance.

        Raises:
            ValueError: If the line is malformed.

        Examples:
            >>> item = GopherItem.from_line(
            ...     b"0About\\t/about\\texample.com\\t70\\r\\n"
            ... )
            >>> item.item_type
            <ItemType.TEXT: '0'>
        """
        # Strip trailing CRLF
        line = line.rstrip(CRLF)

        if not line:
            raise ValueError("Empty line")

        # Decode to string
        try:
            decoded = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded = line.decode("latin-1")

        # First character is the item type
        type_char = decoded[0]
        rest = decoded[1:]

        try:
            item_type = ItemType.from_char(type_char)
        except ValueError:
            # Unknown type - treat as info for compatibility
            item_type = ItemType.INFO

        # Split remaining by tabs
        parts = rest.split("\t")

        if len(parts) < 3:
            # Malformed line - might be info line without full fields
            return cls(
                item_type=item_type,
                display_text=parts[0] if parts else "",
                selector="",
                hostname="",
                port=DEFAULT_PORT,
            )

        display_text = parts[0]
        selector = parts[1]
        hostname = parts[2]

        # Port is optional, default to 70
        port = DEFAULT_PORT
        if len(parts) >= 4 and parts[3]:
            try:
                port = int(parts[3].rstrip("+"))
            except ValueError:
                pass

        # Check for Gopher+ indicator (trailing +)
        gopher_plus = len(parts) >= 4 and parts[3].endswith("+")

        return cls(
            item_type=item_type,
            display_text=display_text,
            selector=selector,
            hostname=hostname,
            port=port,
            gopher_plus=gopher_plus,
        )

    def to_line(self) -> bytes:
        """Serialize this item to a directory listing line.

        Returns:
            The item as bytes, suitable for a Gopher response.
        """
        port_str = str(self.port)
        if self.gopher_plus:
            port_str += "+"

        parts = [
            f"{self.item_type.value}{self.display_text}",
            self.selector,
            self.hostname,
            port_str,
        ]

        return TAB.join(p.encode("utf-8") for p in parts) + CRLF

    @property
    def is_selectable(self) -> bool:
        """Check if this item can be selected/followed."""
        return not self.item_type.is_informational

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return f"[{self.item_type.value}] {self.display_text}"


@dataclass
class GopherResponse:
    """Represents a complete Gopher protocol response.

    A Gopher response can be either:
    - A directory listing (list of GopherItems)
    - Raw content (text file, binary, etc.)

    Attributes:
        items: List of items for directory responses.
        raw_body: Raw response body for non-directory responses.
        is_directory: Whether this is a directory listing.
        attributes: Gopher+ attributes (if requested).

    Examples:
        >>> response = GopherResponse(items=[
        ...     GopherItem(ItemType.TEXT, "Hello", "/hello", "localhost"),
        ... ])
        >>> response.is_directory
        True
    """

    items: list[GopherItem] = field(default_factory=list)
    raw_body: bytes | None = None
    is_directory: bool = True
    attributes: GopherAttributes | None = None

    @classmethod
    def from_bytes(cls, data: bytes, is_directory: bool = True) -> GopherResponse:
        """Parse a Gopher response from raw bytes.

        Args:
            data: The raw response data.
            is_directory: Whether to parse as a directory listing.

        Returns:
            A GopherResponse instance.

        Examples:
            >>> data = b"0Hello\\t/hello\\tlocalhost\\t70\\r\\n.\\r\\n"
            >>> response = GopherResponse.from_bytes(data)
            >>> len(response.items)
            1
        """
        if not is_directory:
            return cls(raw_body=data, is_directory=False)

        items: list[GopherItem] = []

        # Split by lines
        lines = data.split(CRLF)

        for line in lines:
            # Skip empty lines and terminator
            if not line or line == b".":
                continue

            try:
                item = GopherItem.from_line(line)
                items.append(item)
            except ValueError:
                # Skip malformed lines
                continue

        return cls(items=items, is_directory=True)

    def to_bytes(self) -> bytes:
        """Serialize this response to bytes for transmission.

        Returns:
            The response as bytes, ready to send over the network.
        """
        if not self.is_directory:
            return self.raw_body or b""

        parts = [item.to_line() for item in self.items]
        return b"".join(parts) + GOPHER_TERMINATOR

    @property
    def text(self) -> str | None:
        """Get the response body as text (for non-directory responses).

        Returns:
            The body decoded as UTF-8, or None for directory responses.
        """
        if self.is_directory or self.raw_body is None:
            return None

        try:
            return self.raw_body.decode("utf-8")
        except UnicodeDecodeError:
            return self.raw_body.decode("latin-1")

    def __str__(self) -> str:
        """Return a human-readable representation."""
        if self.is_directory:
            return f"GopherDirectory({len(self.items)} items)"
        body_len = len(self.raw_body) if self.raw_body else 0
        return f"GopherResponse({body_len} bytes)"


def create_info_item(text: str, hostname: str = "null.host") -> GopherItem:
    """Create an informational (non-selectable) item.

    Args:
        text: The text to display.
        hostname: Dummy hostname (conventionally "null.host" or "error.host").

    Returns:
        A GopherItem of type INFO.

    Examples:
        >>> item = create_info_item("Welcome to my server!")
        >>> item.item_type
        <ItemType.INFO: 'i'>
    """
    return GopherItem(
        item_type=ItemType.INFO,
        display_text=text,
        selector="",
        hostname=hostname,
        port=0,
    )


def create_error_item(message: str, hostname: str = "error.host") -> GopherItem:
    """Create an error item.

    Args:
        message: The error message to display.
        hostname: Dummy hostname (conventionally "error.host").

    Returns:
        A GopherItem of type ERROR.

    Examples:
        >>> item = create_error_item("File not found")
        >>> item.item_type
        <ItemType.ERROR: '3'>
    """
    return GopherItem(
        item_type=ItemType.ERROR,
        display_text=message,
        selector="",
        hostname=hostname,
        port=0,
    )
