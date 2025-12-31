"""Tests for Gopher client session."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mototli.client.session import GopherClient
from mototli.protocol.constants import DEFAULT_PORT, REQUEST_TIMEOUT
from mototli.protocol.item_types import ItemType
from mototli.protocol.response import GopherItem, GopherResponse


class TestGopherClientInit:
    """Tests for GopherClient initialization."""

    def test_default_timeout(self):
        """Default timeout should be REQUEST_TIMEOUT."""
        client = GopherClient()
        assert client.timeout == REQUEST_TIMEOUT

    def test_custom_timeout(self):
        """Should accept custom timeout."""
        client = GopherClient(timeout=60.0)
        assert client.timeout == 60.0


class TestContextManager:
    """Tests for async context manager."""

    async def test_enter(self):
        """Should return client on enter."""
        client = GopherClient()
        async with client as c:
            assert c is client

    async def test_exit(self):
        """Should exit cleanly."""
        client = GopherClient()
        async with client:
            pass
        # No error means success


class TestGet:
    """Tests for get() method."""

    async def test_get_calls_send_request(self):
        """get() should call _send_request with correct parameters."""
        client = GopherClient()

        # Mock _send_request
        mock_response = GopherResponse(
            items=[GopherItem(ItemType.TEXT, "Test", "/test", "example.com")]
        )
        client._send_request = AsyncMock(return_value=mock_response)

        response = await client.get(
            host="example.com",
            selector="/about",
        )

        assert response == mock_response
        client._send_request.assert_called_once()
        call_kwargs = client._send_request.call_args.kwargs
        assert call_kwargs["host"] == "example.com"
        assert call_kwargs["port"] == DEFAULT_PORT
        assert call_kwargs["is_directory"] is True

    async def test_get_with_port(self):
        """get() should use custom port."""
        client = GopherClient()

        mock_response = GopherResponse(items=[])
        client._send_request = AsyncMock(return_value=mock_response)

        await client.get(
            host="example.com",
            selector="/",
            port=7070,
        )

        call_kwargs = client._send_request.call_args.kwargs
        assert call_kwargs["port"] == 7070

    async def test_get_with_search(self):
        """get() should pass search query."""
        client = GopherClient()

        mock_response = GopherResponse(items=[])
        client._send_request = AsyncMock(return_value=mock_response)

        await client.get(
            host="example.com",
            selector="/search",
            search_query="python",
            item_type=ItemType.SEARCH,
        )

        call_kwargs = client._send_request.call_args.kwargs
        request = call_kwargs["request"]
        assert request.search_query == "python"

    async def test_get_text_item(self):
        """get() with text item type should not be directory."""
        client = GopherClient()

        mock_response = GopherResponse(raw_body=b"Hello", is_directory=False)
        client._send_request = AsyncMock(return_value=mock_response)

        await client.get(
            host="example.com",
            selector="/file.txt",
            item_type=ItemType.TEXT,
        )

        call_kwargs = client._send_request.call_args.kwargs
        assert call_kwargs["is_directory"] is False

    async def test_get_binary_item(self):
        """get() with binary item type should not be directory."""
        client = GopherClient()

        mock_response = GopherResponse(raw_body=b"\x00\x01\x02", is_directory=False)
        client._send_request = AsyncMock(return_value=mock_response)

        await client.get(
            host="example.com",
            selector="/file.bin",
            item_type=ItemType.BINARY,
        )

        call_kwargs = client._send_request.call_args.kwargs
        assert call_kwargs["is_directory"] is False


class TestGetText:
    """Tests for get_text() method."""

    async def test_get_text_returns_string(self):
        """get_text() should return text content."""
        client = GopherClient()

        mock_response = GopherResponse(
            raw_body=b"Hello, World!",
            is_directory=False,
        )
        client.get = AsyncMock(return_value=mock_response)

        text = await client.get_text(
            host="example.com",
            selector="/file.txt",
        )

        assert text == "Hello, World!"

    async def test_get_text_raises_on_directory(self):
        """get_text() should raise if response is directory."""
        client = GopherClient()

        mock_response = GopherResponse(items=[])  # Directory response
        client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="not text"):
            await client.get_text(
                host="example.com",
                selector="/",
            )


class TestGetBinary:
    """Tests for get_binary() method."""

    async def test_get_binary_returns_bytes(self):
        """get_binary() should return raw bytes."""
        client = GopherClient()

        mock_response = GopherResponse(
            raw_body=b"\x00\x01\x02\x03",
            is_directory=False,
        )
        client.get = AsyncMock(return_value=mock_response)

        data = await client.get_binary(
            host="example.com",
            selector="/file.bin",
        )

        assert data == b"\x00\x01\x02\x03"

    async def test_get_binary_empty(self):
        """get_binary() should return empty bytes for empty response."""
        client = GopherClient()

        mock_response = GopherResponse(
            raw_body=None,
            is_directory=False,
        )
        client.get = AsyncMock(return_value=mock_response)

        data = await client.get_binary(
            host="example.com",
            selector="/empty",
        )

        assert data == b""


class TestGetAttributes:
    """Tests for get_attributes() method."""

    async def test_get_attributes_parses_block(self):
        """get_attributes() should parse Gopher+ attributes."""
        client = GopherClient()

        attr_data = b"+INFO: 0About\t/about\texample.com\t70\r\n"
        client._send_raw_request = AsyncMock(return_value=attr_data)

        attrs = await client.get_attributes(
            host="example.com",
            selector="/about",
        )

        assert attrs.info is not None
        assert attrs.info.display_text == "About"


class TestGetWithView:
    """Tests for get_with_view() method."""

    async def test_get_with_view_sets_view_type(self):
        """get_with_view() should set view type in request."""
        client = GopherClient()

        mock_response = GopherResponse(raw_body=b"content", is_directory=False)
        client._send_request = AsyncMock(return_value=mock_response)

        await client.get_with_view(
            host="example.com",
            selector="/doc",
            view_type="text/plain",
        )

        call_kwargs = client._send_request.call_args.kwargs
        request = call_kwargs["request"]
        assert request.view_type == "text/plain"


class TestSendRawRequest:
    """Tests for _send_raw_request() method."""

    async def test_creates_connection(self):
        """Should create connection with correct parameters."""
        client = GopherClient()

        with patch("mototli.client.session.asyncio") as mock_asyncio:
            # Set up mock
            mock_loop = Mock()
            mock_future = asyncio.Future()
            mock_future.set_result(b"response data")
            mock_loop.create_future.return_value = mock_future

            mock_transport = Mock()
            mock_protocol = Mock()

            async def mock_wait_for(coro, timeout):
                return await coro

            async def mock_create_connection(*args, **kwargs):
                return (mock_transport, mock_protocol)

            mock_loop.create_connection = mock_create_connection
            mock_asyncio.get_running_loop.return_value = mock_loop
            mock_asyncio.wait_for = mock_wait_for

            from mototli.protocol.request import GopherRequest

            request = GopherRequest(selector="/about")

            result = await client._send_raw_request(
                host="example.com",
                port=70,
                request=request,
                is_directory=True,
            )

            assert result == b"response data"
            mock_transport.close.assert_called_once()

    async def test_raises_timeout_on_connect_timeout(self):
        """Should raise TimeoutError on connection timeout."""
        client = GopherClient(timeout=0.001)

        with patch("mototli.client.session.asyncio") as mock_asyncio:
            mock_loop = Mock()
            mock_future = asyncio.Future()
            mock_loop.create_future.return_value = mock_future

            async def mock_wait_for(coro, timeout):
                raise TimeoutError("Timed out")

            mock_asyncio.get_running_loop.return_value = mock_loop
            mock_asyncio.wait_for = mock_wait_for

            from mototli.protocol.request import GopherRequest

            request = GopherRequest(selector="/")

            with pytest.raises(TimeoutError, match="Connection timeout"):
                await client._send_raw_request(
                    host="example.com",
                    port=70,
                    request=request,
                    is_directory=True,
                )

    async def test_raises_connection_error(self):
        """Should raise ConnectionError on connection failure."""
        client = GopherClient()

        with patch("mototli.client.session.asyncio") as mock_asyncio:
            mock_loop = Mock()
            mock_future = asyncio.Future()
            mock_loop.create_future.return_value = mock_future

            async def mock_wait_for(coro, timeout):
                raise OSError("Connection refused")

            mock_asyncio.get_running_loop.return_value = mock_loop
            mock_asyncio.wait_for = mock_wait_for

            from mototli.protocol.request import GopherRequest

            request = GopherRequest(selector="/")

            with pytest.raises(ConnectionError, match="Connection failed"):
                await client._send_raw_request(
                    host="example.com",
                    port=70,
                    request=request,
                    is_directory=True,
                )


class TestSendRequest:
    """Tests for _send_request() method."""

    async def test_parses_directory_response(self):
        """Should parse directory response."""
        client = GopherClient()

        raw_data = b"0About\t/about\texample.com\t70\r\n.\r\n"
        client._send_raw_request = AsyncMock(return_value=raw_data)

        from mototli.protocol.request import GopherRequest

        request = GopherRequest(selector="/")

        response = await client._send_request(
            host="example.com",
            port=70,
            request=request,
            is_directory=True,
        )

        assert response.is_directory is True
        assert len(response.items) == 1
        assert response.items[0].display_text == "About"

    async def test_parses_text_response(self):
        """Should parse text response."""
        client = GopherClient()

        raw_data = b"Hello, World!"
        client._send_raw_request = AsyncMock(return_value=raw_data)

        from mototli.protocol.request import GopherRequest

        request = GopherRequest(selector="/file.txt")

        response = await client._send_request(
            host="example.com",
            port=70,
            request=request,
            is_directory=False,
        )

        assert response.is_directory is False
        assert response.raw_body == b"Hello, World!"


@pytest.mark.integration
@pytest.mark.network
class TestIntegration:
    """Integration tests requiring network access."""

    @pytest.mark.skip(reason="Requires network access")
    async def test_real_server(self):
        """Test against a real Gopher server."""
        async with GopherClient(timeout=10.0) as client:
            response = await client.get("gopher.floodgap.com")
            assert response.is_directory
            assert len(response.items) > 0
