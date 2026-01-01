"""Tests for GopherServerProtocol."""

import asyncio
from unittest.mock import Mock

import pytest

from mototli.protocol.constants import CRLF, MAX_SELECTOR_SIZE
from mototli.protocol.item_types import ItemType
from mototli.protocol.request import GopherRequest
from mototli.protocol.response import GopherItem, GopherResponse, create_error_item
from mototli.server.protocol import GopherPlusServerProtocol, GopherServerProtocol


class TestGopherServerProtocolCreation:
    """Tests for GopherServerProtocol initialization."""

    def test_init_with_handler(self):
        """Initialize protocol with request handler."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)

        assert protocol.request_handler == handler
        assert protocol.transport is None
        assert protocol.buffer == b""

    def test_init_with_custom_timeout(self):
        """Initialize with custom timeout."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(
            request_handler=handler,
            request_timeout=60.0,
        )

        assert protocol.request_timeout == 60.0

    def test_default_timeout(self):
        """Default timeout is used when not specified."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)

        assert protocol.request_timeout == 30.0  # Default from module


class TestConnectionMade:
    """Tests for connection_made callback."""

    def test_stores_transport(self, mock_transport: Mock):
        """Transport is stored on connection."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        assert protocol.transport == mock_transport

    def test_stores_peer_name(self, mock_transport: Mock):
        """Peer name is extracted from transport."""
        mock_transport.get_extra_info.return_value = ("192.168.1.100", 54321)

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        assert protocol.peer_name == ("192.168.1.100", 54321)
        mock_transport.get_extra_info.assert_called_with("peername")

    def test_stores_request_start_time(self, mock_transport: Mock):
        """Request start time is recorded."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        assert protocol.request_start_time is not None


class TestDataReceived:
    """Tests for data_received callback."""

    def test_accumulates_data(self, mock_transport: Mock):
        """Data is accumulated in buffer."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        protocol.data_received(b"/path")
        assert protocol.buffer == b"/path"

        protocol.data_received(b"/more")
        assert protocol.buffer == b"/path/more"

    def test_complete_request_processed(self, mock_transport: Mock):
        """Complete request triggers processing."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "test", "", "host")],
                is_directory=True,
            )

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        # Send complete request
        protocol.data_received(b"/test\r\n")

        # Transport should have received response
        mock_transport.write.assert_called()
        mock_transport.close.assert_called()

    def test_fragmented_request(self, mock_transport: Mock):
        """Fragmented request is buffered until complete."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "test", "", "host")],
                is_directory=True,
            )

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        # Send partial data
        protocol.data_received(b"/test")
        mock_transport.write.assert_not_called()

        # Send more partial data
        protocol.data_received(b"/more")
        mock_transport.write.assert_not_called()

        # Complete the request
        protocol.data_received(b"\r\n")
        mock_transport.write.assert_called()

    def test_oversized_request_rejected(self, mock_transport: Mock):
        """Request exceeding max size is rejected."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        # Send oversized data
        oversized = b"x" * (MAX_SELECTOR_SIZE + 100)
        protocol.data_received(oversized)

        # Should have sent error response
        mock_transport.write.assert_called()
        call_args = mock_transport.write.call_args[0][0]
        assert b"maximum size" in call_args.lower()


class TestRequestHandling:
    """Tests for request processing."""

    def test_parse_simple_request(self, mock_transport: Mock):
        """Parse and process simple selector request."""
        received_request = None

        def handler(request: GopherRequest) -> GopherResponse:
            nonlocal received_request
            received_request = request
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/about\r\n")

        assert received_request is not None
        assert received_request.selector == "/about"

    def test_parse_request_with_search(self, mock_transport: Mock):
        """Parse request with search query."""
        received_request = None

        def handler(request: GopherRequest) -> GopherResponse:
            nonlocal received_request
            received_request = request
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/search\tquery string\r\n")

        assert received_request.selector == "/search"
        assert received_request.search_query == "query string"

    def test_parse_gopher_plus_request(self, mock_transport: Mock):
        """Parse Gopher+ request."""
        received_request = None

        def handler(request: GopherRequest) -> GopherResponse:
            nonlocal received_request
            received_request = request
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/doc\t+\r\n")

        assert received_request.is_gopher_plus is True

    def test_client_ip_attached(self, mock_transport: Mock):
        """Client IP is attached to request."""
        mock_transport.get_extra_info.return_value = ("10.0.0.1", 12345)
        received_request = None

        def handler(request: GopherRequest) -> GopherResponse:
            nonlocal received_request
            received_request = request
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/test\r\n")

        assert received_request.client_ip == "10.0.0.1"

    def test_handler_exception_returns_error(self, mock_transport: Mock):
        """Handler exception returns error response."""

        def handler(request: GopherRequest) -> GopherResponse:
            raise RuntimeError("Handler error")

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/test\r\n")

        # Should have sent error response
        call_args = mock_transport.write.call_args[0][0]
        assert b"Server error" in call_args


class TestSendResponse:
    """Tests for response sending."""

    def test_send_directory_response(self, mock_transport: Mock):
        """Send directory listing response."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[
                    GopherItem(ItemType.TEXT, "File", "/file", "host"),
                    GopherItem(ItemType.DIRECTORY, "Dir", "/dir", "host"),
                ],
                is_directory=True,
            )

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/\r\n")

        call_args = mock_transport.write.call_args[0][0]
        assert b"0File" in call_args
        assert b"1Dir" in call_args
        assert call_args.endswith(b".\r\n")

    def test_send_text_response(self, mock_transport: Mock):
        """Send text file response."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                raw_body=b"Hello, World!",
                is_directory=False,
            )

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/file.txt\r\n")

        call_args = mock_transport.write.call_args[0][0]
        assert call_args == b"Hello, World!"

    def test_send_binary_response(self, mock_transport: Mock):
        """Send binary file response."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                raw_body=b"\x00\x01\x02\xff\xfe",
                is_directory=False,
            )

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/file.bin\r\n")

        call_args = mock_transport.write.call_args[0][0]
        assert call_args == b"\x00\x01\x02\xff\xfe"

    def test_closes_connection_after_response(self, mock_transport: Mock):
        """Connection is closed after sending response."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/\r\n")

        mock_transport.close.assert_called_once()

    def test_send_error_response(self, mock_transport: Mock):
        """Send error response correctly."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[create_error_item("Not found")],
                is_directory=True,
            )

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/missing\r\n")

        call_args = mock_transport.write.call_args[0][0]
        assert b"3Not found" in call_args


class TestConnectionLost:
    """Tests for connection_lost callback."""

    def test_cleans_up_transport(self, mock_transport: Mock):
        """Transport reference is cleared."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        protocol.connection_lost(None)

        assert protocol.transport is None

    def test_handles_exception(self, mock_transport: Mock):
        """Exception in connection_lost is handled."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        # Should not raise
        protocol.connection_lost(ConnectionResetError())

        assert protocol.transport is None


class TestClientIP:
    """Tests for client_ip property."""

    def test_client_ip_property(self, mock_transport: Mock):
        """client_ip property returns IP from peer_name."""
        mock_transport.get_extra_info.return_value = ("1.2.3.4", 5678)

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)

        assert protocol.client_ip == "1.2.3.4"

    def test_client_ip_unknown(self):
        """client_ip returns 'unknown' when peer_name is None."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        protocol = GopherServerProtocol(request_handler=handler)
        # No connection made, so peer_name is None

        assert protocol.client_ip == "unknown"


class TestGopherPlusServerProtocol:
    """Tests for GopherPlusServerProtocol."""

    def test_inherits_from_base(self):
        """Inherits from GopherServerProtocol."""
        assert issubclass(GopherPlusServerProtocol, GopherServerProtocol)

    def test_sends_attributes_before_content(self, mock_transport: Mock):
        """Sends attribute block before content for Gopher+."""
        from mototli.protocol.attributes import GopherAttributes

        def handler(request: GopherRequest) -> GopherResponse:
            # Create a GopherItem for the info field
            info_item = GopherItem(
                item_type=ItemType.TEXT,
                display_text="Test",
                selector="/test",
                hostname="host",
                port=70,
            )
            attrs = GopherAttributes(info=info_item)
            return GopherResponse(
                raw_body=b"File content",
                is_directory=False,
                attributes=attrs,
            )

        protocol = GopherPlusServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/test\t+\r\n")

        # Should have multiple write calls (attrs, separator, content)
        assert mock_transport.write.call_count >= 2

        # First call should contain attributes
        first_call = mock_transport.write.call_args_list[0][0][0]
        assert b"+INFO" in first_call

    def test_separator_between_attributes_and_content(self, mock_transport: Mock):
        """Adds CRLF separator between attributes and content."""
        from mototli.protocol.attributes import GopherAttributes

        def handler(request: GopherRequest) -> GopherResponse:
            info_item = GopherItem(
                item_type=ItemType.TEXT,
                display_text="Test",
                selector="/test",
                hostname="host",
                port=70,
            )
            attrs = GopherAttributes(info=info_item)
            return GopherResponse(
                raw_body=b"File content",
                is_directory=False,
                attributes=attrs,
            )

        protocol = GopherPlusServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/test\t+\r\n")

        # Second call should be CRLF separator
        calls = mock_transport.write.call_args_list
        if len(calls) >= 2:
            second_call = calls[1][0][0]
            assert second_call == CRLF

    def test_directory_response_no_attributes_header(self, mock_transport: Mock):
        """Directory response doesn't include separate attributes."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.TEXT, "Test", "/test", "host")],
                is_directory=True,
            )

        protocol = GopherPlusServerProtocol(request_handler=handler)
        protocol.connection_made(mock_transport)
        protocol.data_received(b"/\r\n")

        # Should have single write call (just directory listing)
        assert mock_transport.write.call_count == 1
