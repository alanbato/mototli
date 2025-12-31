"""Tests for Gopher client protocol."""

import asyncio
from unittest.mock import Mock

import pytest

from mototli.client.protocol import GopherClientProtocol, GopherPlusClientProtocol
from mototli.protocol.request import GopherRequest, RequestType


class TestGopherClientProtocolInit:
    """Tests for GopherClientProtocol initialization."""

    def test_init(self):
        """Initialize protocol with request and future."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/about")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
            is_directory=True,
        )

        assert protocol.request == request
        assert protocol.response_future == future
        assert protocol.is_directory is True
        assert protocol.buffer == b""
        assert protocol.transport is None

        loop.close()

    def test_init_non_directory(self):
        """Initialize protocol for non-directory request."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/file.txt")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
            is_directory=False,
        )

        assert protocol.is_directory is False

        loop.close()


class TestConnectionMade:
    """Tests for connection_made callback."""

    def test_sends_request(self):
        """Should send request when connection is made."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/about")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        # Mock transport
        transport = Mock()
        protocol.connection_made(transport)

        # Verify transport was stored
        assert protocol.transport == transport

        # Verify request was sent
        transport.write.assert_called_once_with(b"/about\r\n")

        loop.close()

    def test_sends_request_with_search(self):
        """Should send request with search query."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/search", search_query="python")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        transport = Mock()
        protocol.connection_made(transport)

        transport.write.assert_called_once_with(b"/search\tpython\r\n")

        loop.close()

    def test_sends_gopher_plus_request(self):
        """Should send Gopher+ request."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(
            selector="/about",
            request_type=RequestType.PLUS,
        )

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        transport = Mock()
        protocol.connection_made(transport)

        transport.write.assert_called_once_with(b"/about\t+\r\n")

        loop.close()


class TestDataReceived:
    """Tests for data_received callback."""

    def test_accumulates_data(self):
        """Should accumulate received data in buffer."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
            is_directory=False,
        )

        transport = Mock()
        protocol.connection_made(transport)

        protocol.data_received(b"Hello, ")
        assert protocol.buffer == b"Hello, "

        protocol.data_received(b"World!")
        assert protocol.buffer == b"Hello, World!"

        loop.close()

    def test_closes_on_directory_terminator(self):
        """Should close connection when directory terminator received."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
            is_directory=True,
        )

        transport = Mock()
        protocol.connection_made(transport)

        protocol.data_received(b"0About\t/about\texample.com\t70\r\n.\r\n")

        transport.close.assert_called_once()

        loop.close()

    def test_does_not_close_for_non_directory(self):
        """Should not close on terminator for non-directory response."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/file.txt")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
            is_directory=False,
        )

        transport = Mock()
        protocol.connection_made(transport)

        # For text files, terminator is just content
        protocol.data_received(b"Line 1\r\n.\r\nLine 2")

        transport.close.assert_not_called()
        assert protocol.buffer == b"Line 1\r\n.\r\nLine 2"

        loop.close()

    def test_closes_on_max_size_exceeded(self):
        """Should close connection when max response size exceeded."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        transport = Mock()
        protocol.connection_made(transport)

        # Send more than MAX_RESPONSE_BODY_SIZE
        large_data = b"x" * (10 * 1024 * 1024 + 1)
        protocol.data_received(large_data)

        transport.close.assert_called_once()

        loop.close()


class TestEofReceived:
    """Tests for eof_received callback."""

    def test_returns_false(self):
        """Should return False to close connection."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        result = protocol.eof_received()
        assert result is False

        loop.close()


class TestConnectionLost:
    """Tests for connection_lost callback."""

    def test_sets_result_on_clean_close(self):
        """Should set result when connection closes cleanly."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        transport = Mock()
        protocol.connection_made(transport)
        protocol.data_received(b"0About\t/about\texample.com\t70\r\n")
        protocol.connection_lost(None)

        assert future.done()
        assert future.result() == b"0About\t/about\texample.com\t70\r\n"

        loop.close()

    def test_sets_exception_on_error(self):
        """Should set exception when connection closes with error."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(selector="/")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        transport = Mock()
        protocol.connection_made(transport)

        error = ConnectionError("Connection reset")
        protocol.connection_lost(error)

        assert future.done()
        with pytest.raises(ConnectionError):
            future.result()

        loop.close()

    def test_does_not_set_twice(self):
        """Should not set result if future is already done."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        future.set_result(b"already set")
        request = GopherRequest(selector="/")

        protocol = GopherClientProtocol(
            request=request,
            response_future=future,
        )

        # Should not raise
        protocol.connection_lost(None)

        assert future.result() == b"already set"

        loop.close()


class TestGopherPlusClientProtocol:
    """Tests for GopherPlusClientProtocol."""

    def test_init(self):
        """Initialize Gopher+ protocol."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(
            selector="/about",
            request_type=RequestType.ATTRIBUTES,
        )

        protocol = GopherPlusClientProtocol(
            request=request,
            response_future=future,
        )

        assert protocol.request == request
        assert protocol.attributes_complete is False
        assert protocol.content_started is False

        loop.close()

    def test_handles_error_response(self):
        """Should close on Gopher+ error response (starts with --)."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(
            selector="/about",
            request_type=RequestType.PLUS,
        )

        protocol = GopherPlusClientProtocol(
            request=request,
            response_future=future,
        )

        transport = Mock()
        protocol.connection_made(transport)

        protocol.data_received(b"--1 Item not found\r\n")

        transport.close.assert_called_once()

        loop.close()

    def test_accumulates_attributes(self):
        """Should accumulate Gopher+ attribute data."""
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        request = GopherRequest(
            selector="/about",
            request_type=RequestType.ATTRIBUTES,
        )

        protocol = GopherPlusClientProtocol(
            request=request,
            response_future=future,
            is_directory=False,
        )

        transport = Mock()
        protocol.connection_made(transport)

        protocol.data_received(b"+INFO: 0About\t/about\texample.com\t70\r\n")
        protocol.data_received(b"+ADMIN:\r\n Admin: John\r\n")

        assert b"+INFO:" in protocol.buffer
        assert b"+ADMIN:" in protocol.buffer

        loop.close()
