"""Low-level Gopher client protocol implementation.

This module implements the Gopher client protocol using asyncio's
Protocol/Transport pattern for efficient, non-blocking I/O.
"""

import asyncio

from ..protocol.constants import GOPHER_TERMINATOR, MAX_RESPONSE_BODY_SIZE
from ..protocol.request import GopherRequest


class GopherClientProtocol(asyncio.Protocol):
    """Client-side protocol for making Gopher requests.

    This class implements asyncio.Protocol for handling Gopher client connections.
    It manages the connection lifecycle, sends requests, and accumulates responses.

    The Gopher protocol is simpler than Gemini:
    1. Client connects via TCP (no TLS)
    2. Client sends selector + CRLF
    3. Server sends response body
    4. Connection closes

    For directory listings, the response ends with a single "." on a line.
    For other content, the response continues until connection closes.

    Attributes:
        request: The GopherRequest being made.
        response_future: Future that will be set with the raw response bytes.
        transport: The transport handling the connection.
        buffer: Buffer for accumulating incoming data.
        is_directory: Whether we expect a directory response.
    """

    def __init__(
        self,
        request: GopherRequest,
        response_future: "asyncio.Future[bytes]",
        is_directory: bool = True,
    ):
        """Initialize the client protocol.

        Args:
            request: The Gopher request to send.
            response_future: Future to set with the raw response bytes.
            is_directory: Whether to expect a directory listing response.
        """
        self.request = request
        self.response_future = response_future
        self.transport: asyncio.Transport | None = None
        self.buffer = b""
        self.is_directory = is_directory

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Called when connection to server is established.

        Sends the Gopher request (selector + optional search + CRLF).

        Args:
            transport: The transport handling this connection.
        """
        self.transport = transport  # type: ignore[assignment]

        # Send Gopher request
        request_bytes = self.request.to_bytes()
        if self.transport:
            self.transport.write(request_bytes)

    def data_received(self, data: bytes) -> None:
        """Called when data is received from the server.

        This method may be called multiple times as data arrives. We accumulate
        data in a buffer until the connection closes.

        Args:
            data: Raw bytes received from the server.
        """
        self.buffer += data

        # Check if we've received the directory terminator
        if self.is_directory and self.buffer.endswith(GOPHER_TERMINATOR):
            # Directory response complete
            if self.transport:
                self.transport.close()
            return

        # Check if we've received too much data (prevent memory exhaustion)
        if len(self.buffer) > MAX_RESPONSE_BODY_SIZE:
            self._set_error(
                Exception(
                    f"Response body exceeds maximum size ({MAX_RESPONSE_BODY_SIZE} bytes)"
                )
            )
            if self.transport:
                self.transport.close()

    def eof_received(self) -> bool:
        """Called when the server closes its write side (graceful shutdown).

        Returns:
            False to close our write side too (full connection close).
        """
        return False  # Don't keep connection open

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection is closed.

        Sets the response result in the future. This is where we deliver
        the final response to the higher-level async code.

        Args:
            exc: Exception if connection closed due to error, None for clean close.
        """
        # If the future is already done (error case), don't set it again
        if self.response_future.done():
            return

        # If there was a connection error, set the exception
        if exc:
            self.response_future.set_exception(exc)
            return

        # Set the raw response bytes
        self.response_future.set_result(self.buffer)

    def _set_error(self, exc: Exception) -> None:
        """Set an error in the response future.

        Args:
            exc: The exception to set.
        """
        if not self.response_future.done():
            self.response_future.set_exception(exc)


class GopherPlusClientProtocol(GopherClientProtocol):
    """Client protocol for Gopher+ requests.

    Gopher+ responses include attribute blocks that need special parsing.
    The response format for Gopher+ is:
    - Attribute block (starting with +INFO:, etc.)
    - Followed by content (if not attributes-only request)

    For attributes-only requests (modifier=!), only the attribute block is returned.
    For regular Gopher+ requests (modifier=+), both attributes and content are returned.
    """

    def __init__(
        self,
        request: GopherRequest,
        response_future: "asyncio.Future[bytes]",
        is_directory: bool = True,
    ):
        """Initialize the Gopher+ client protocol.

        Args:
            request: The Gopher+ request to send.
            response_future: Future to set with the raw response bytes.
            is_directory: Whether to expect a directory listing response.
        """
        super().__init__(request, response_future, is_directory)
        self.attributes_complete = False
        self.content_started = False

    def data_received(self, data: bytes) -> None:
        """Called when data is received from the server.

        Gopher+ responses may include an attribute block followed by content.
        We need to handle both parts appropriately.

        Args:
            data: Raw bytes received from the server.
        """
        self.buffer += data

        # Check for Gopher+ error response (starts with --)
        if self.buffer.startswith(b"--") and b"\r\n" in self.buffer:
            # Error response - close connection
            if self.transport:
                self.transport.close()
            return

        # Check if we've received the directory terminator
        if self.is_directory and self.buffer.endswith(GOPHER_TERMINATOR):
            if self.transport:
                self.transport.close()
            return

        # Check size limit
        if len(self.buffer) > MAX_RESPONSE_BODY_SIZE:
            self._set_error(
                Exception(
                    f"Response body exceeds maximum size ({MAX_RESPONSE_BODY_SIZE} bytes)"
                )
            )
            if self.transport:
                self.transport.close()
