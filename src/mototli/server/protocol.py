"""Low-level Gopher server protocol implementation.

This module implements the Gopher server protocol using asyncio's
Protocol/Transport pattern for efficient, non-blocking I/O.
"""

import asyncio
import time
from collections.abc import Callable

from ..protocol.constants import CRLF, MAX_SELECTOR_SIZE
from ..protocol.request import GopherRequest
from ..protocol.response import GopherResponse

# Connection timeout in seconds
REQUEST_TIMEOUT = 30.0


class GopherServerProtocol(asyncio.Protocol):
    """Server-side protocol for handling Gopher requests.

    This class implements asyncio.Protocol for handling Gopher server connections.
    It manages the connection lifecycle, receives requests, and sends responses.

    The protocol follows the Gopher specification (RFC 1436):
    1. Client connects via TCP
    2. Client sends selector + CRLF
    3. Server sends response body
    4. Connection closes

    For directory listings, the response ends with a single "." on a line.
    For other content, the response continues until connection closes.

    Attributes:
        request_handler: Callback function that takes a GopherRequest and
            returns a GopherResponse.
        transport: The transport handling the connection.
        buffer: Buffer for accumulating incoming data.
        peer_name: Remote peer address information.
        request_timeout: Timeout for receiving requests in seconds.

    Examples:
        >>> def handler(request: GopherRequest) -> GopherResponse:
        ...     return GopherResponse(items=[...], is_directory=True)
        >>> protocol = GopherServerProtocol(handler)
    """

    def __init__(
        self,
        request_handler: Callable[[GopherRequest], GopherResponse],
        request_timeout: float = REQUEST_TIMEOUT,
    ) -> None:
        """Initialize the server protocol.

        Args:
            request_handler: Callback that processes requests and returns responses.
            request_timeout: Timeout for receiving requests in seconds.
        """
        self.request_handler = request_handler
        self.request_timeout = request_timeout
        self.transport: asyncio.Transport | None = None
        self.buffer = b""
        self.peer_name: tuple[str, int] | None = None
        self.request_start_time: float | None = None
        self.timeout_handle: asyncio.TimerHandle | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Called when a client connects.

        Args:
            transport: The transport handling this connection.
        """
        self.transport = transport  # type: ignore[assignment]
        if self.transport:
            self.peer_name = self.transport.get_extra_info("peername")
        self.request_start_time = time.time()

        # Set timeout for receiving request
        try:
            loop = asyncio.get_running_loop()
            self.timeout_handle = loop.call_later(
                self.request_timeout, self._handle_timeout
            )
        except RuntimeError:
            # No event loop running (probably in tests)
            self.timeout_handle = None

    def data_received(self, data: bytes) -> None:
        """Called when data is received from the client.

        This method may be called multiple times as data arrives. We accumulate
        data in a buffer until we receive a complete request (selector + CRLF).

        Args:
            data: Raw bytes received from the client.
        """
        self.buffer += data

        # Check if request exceeds maximum size (prevent DoS)
        if len(self.buffer) > MAX_SELECTOR_SIZE + len(CRLF):
            self._send_error_response("Request exceeds maximum size")
            return

        # Check if we have a complete request (ends with CRLF)
        if CRLF in self.buffer:
            # Cancel timeout - we got the request
            if self.timeout_handle:
                self.timeout_handle.cancel()
                self.timeout_handle = None

            request_line, _ = self.buffer.split(CRLF, 1)
            self._handle_request(request_line)

    def _handle_request(self, request_line: bytes) -> None:
        """Process the Gopher request and send response.

        Args:
            request_line: The request line as bytes.
        """
        try:
            # Parse request
            request = GopherRequest.from_line(request_line)
        except ValueError as e:
            self._send_error_response(f"Invalid request: {e}")
            return

        # Attach client IP
        if self.peer_name:
            request.client_ip = self.peer_name[0]

        try:
            # Call request handler to get response
            response = self.request_handler(request)
        except Exception as e:
            # Catch any handler errors
            self._send_error_response(f"Server error: {e}")
            return

        # Send the response
        self._send_response(response)

    def _send_response(self, response: GopherResponse) -> None:
        """Send a GopherResponse to the client.

        Args:
            response: The response to send.
        """
        if not self.transport:
            return

        # Serialize and send response
        response_bytes = response.to_bytes()
        self.transport.write(response_bytes)

        # Close connection (Gopher: one request per connection)
        self.transport.close()

    def _send_error_response(self, message: str) -> None:
        """Send an error response and close the connection.

        Args:
            message: The error message.
        """
        if not self.transport:
            return

        from ..protocol.response import create_error_item

        # Create error response
        response = GopherResponse(
            items=[create_error_item(message)],
            is_directory=True,
        )
        self._send_response(response)

    def _handle_timeout(self) -> None:
        """Handle request timeout."""
        if self.transport and not self.transport.is_closing():
            self._send_error_response("Request timeout")

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection is closed.

        Args:
            exc: Exception if connection closed due to error, None for clean close.
        """
        # Cancel timeout if still active
        if self.timeout_handle:
            self.timeout_handle.cancel()
            self.timeout_handle = None

        # Cleanup
        self.transport = None

    @property
    def client_ip(self) -> str:
        """Get the client's IP address."""
        return self.peer_name[0] if self.peer_name else "unknown"


class GopherPlusServerProtocol(GopherServerProtocol):
    """Server protocol with enhanced Gopher+ support.

    This protocol extends the base GopherServerProtocol with special
    handling for Gopher+ requests and responses.
    """

    def _send_response(self, response: GopherResponse) -> None:
        """Send a GopherResponse to the client.

        For Gopher+ responses, may include attribute headers before content.

        Args:
            response: The response to send.
        """
        if not self.transport:
            return

        # For Gopher+ attribute responses, send attributes first
        if response.attributes and not response.is_directory:
            # Send attribute block
            attr_bytes = response.attributes.to_string().encode("utf-8")
            self.transport.write(attr_bytes)

            # If there's also content, add separator
            if response.raw_body:
                self.transport.write(CRLF)

        # Send main response content
        response_bytes = response.to_bytes()
        self.transport.write(response_bytes)

        # Close connection
        self.transport.close()
