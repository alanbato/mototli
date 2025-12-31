"""Gopher protocol request representation.

This module provides the GopherRequest dataclass for representing
Gopher protocol requests, including Gopher+ extensions.
"""

from dataclasses import dataclass, field
from enum import Enum

from .constants import CRLF, MAX_SELECTOR_SIZE, TAB


class RequestType(str, Enum):
    """Gopher+ request type modifiers.

    These modifiers change the behavior of Gopher+ requests:
    - STANDARD: Normal Gopher request (no modifier)
    - PLUS: Request with Gopher+ attributes and content
    - ATTRIBUTES: Request Gopher+ attributes only (no content)
    - DIRECTORY: Request directory entry for the item
    """

    STANDARD = ""
    """Normal Gopher request."""

    PLUS = "+"
    """Gopher+ request with content and attributes."""

    ATTRIBUTES = "!"
    """Request Gopher+ attributes only."""

    DIRECTORY = "$"
    """Request directory entry for item."""


@dataclass
class GopherRequest:
    """Represents a Gopher protocol request.

    A Gopher request consists of:
    - A selector string (path to the resource)
    - Optional search query (for type 7 search servers)
    - Optional Gopher+ modifier

    The wire format is: selector[TAB search][TAB modifier]CRLF

    Attributes:
        selector: The resource selector (path).
        search_query: Optional search query for type 7 servers.
        request_type: Gopher+ request type modifier.
        view_type: Gopher+ specific view type to request.
        client_ip: IP address of the client (server-side only).

    Examples:
        >>> request = GopherRequest.from_line(b"/about")
        >>> request.selector
        '/about'

        >>> request = GopherRequest.from_line(b"/search\\tpython")
        >>> request.search_query
        'python'
    """

    selector: str
    search_query: str | None = None
    request_type: RequestType = RequestType.STANDARD
    view_type: str | None = None
    client_ip: str | None = field(default=None, compare=False)

    @classmethod
    def from_line(cls, line: bytes) -> "GopherRequest":
        """Parse a Gopher request from a request line.

        Args:
            line: The request line (without trailing CRLF).

        Returns:
            A GopherRequest instance.

        Raises:
            ValueError: If the request line is invalid or too long.

        Examples:
            >>> request = GopherRequest.from_line(b"/")
            >>> request.selector
            '/'

            >>> request = GopherRequest.from_line(b"/search\\tquery\\t+")
            >>> request.request_type
            <RequestType.PLUS: '+'>
        """
        # Strip any trailing CRLF if present
        line = line.rstrip(CRLF)

        # Check size limit
        if len(line) > MAX_SELECTOR_SIZE:
            raise ValueError(
                f"Request exceeds maximum size: {len(line)} > {MAX_SELECTOR_SIZE}"
            )

        # Decode to string
        try:
            decoded = line.decode("utf-8")
        except UnicodeDecodeError:
            # Fall back to latin-1 for compatibility
            decoded = line.decode("latin-1")

        # Split by tabs
        parts = decoded.split("\t")

        selector = parts[0] if parts else ""
        search_query: str | None = None
        request_type = RequestType.STANDARD
        view_type: str | None = None

        if len(parts) >= 2:
            second = parts[1]
            # Check if it's a Gopher+ modifier or search query
            if second in ("", "+", "!", "$"):
                request_type = RequestType(second) if second else RequestType.STANDARD
            elif second.startswith("+") and len(second) > 1:
                # View type request: +viewtype
                request_type = RequestType.PLUS
                view_type = second[1:]
            else:
                search_query = second

        if len(parts) >= 3:
            third = parts[2]
            if third in ("+", "!", "$"):
                request_type = RequestType(third)
            elif third.startswith("+") and len(third) > 1:
                request_type = RequestType.PLUS
                view_type = third[1:]

        return cls(
            selector=selector,
            search_query=search_query,
            request_type=request_type,
            view_type=view_type,
        )

    def to_bytes(self) -> bytes:
        """Serialize the request to bytes for transmission.

        Returns:
            The request as bytes, ready to send over the network.

        Examples:
            >>> request = GopherRequest(selector="/about")
            >>> request.to_bytes()
            b'/about\\r\\n'
        """
        parts = [self.selector]

        if self.search_query is not None:
            parts.append(self.search_query)

        if self.request_type != RequestType.STANDARD:
            if self.view_type:
                parts.append(f"+{self.view_type}")
            else:
                parts.append(self.request_type.value)

        return TAB.join(p.encode("utf-8") for p in parts) + CRLF

    @property
    def is_gopher_plus(self) -> bool:
        """Check if this is a Gopher+ request."""
        return self.request_type != RequestType.STANDARD

    def __str__(self) -> str:
        """Return a human-readable string representation of the request."""
        parts = [f"Selector: {self.selector}"]
        if self.search_query:
            parts.append(f"Search: {self.search_query}")
        if self.is_gopher_plus:
            parts.append(f"Type: {self.request_type.name}")
        if self.view_type:
            parts.append(f"View: {self.view_type}")
        return " | ".join(parts)
