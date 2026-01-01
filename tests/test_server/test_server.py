"""Tests for GopherServer."""

import asyncio
from pathlib import Path

import pytest

from mototli.server import GopherServer
from mototli.server.config import ServerConfig
from mototli.server.router import RouteType


class TestGopherServerCreation:
    """Tests for GopherServer initialization."""

    def test_init_with_config(self, basic_config: ServerConfig):
        """Initialize server with configuration."""
        server = GopherServer(basic_config)

        assert server.config == basic_config
        assert server.server is None  # Not started yet

    def test_creates_router(self, basic_config: ServerConfig):
        """Router is created on initialization."""
        server = GopherServer(basic_config)

        assert server.router is not None
        assert len(server.router.routes) > 0

    def test_sets_up_routes(self, basic_config: ServerConfig):
        """Default routes are configured."""
        server = GopherServer(basic_config)

        # Should have at least one route
        assert len(server.router.routes) > 0

        # Should have default handler
        assert server.router.default_handler is not None


class TestGopherServerRoutes:
    """Tests for route setup."""

    def test_cgi_routes_added(self, config_with_cgi: ServerConfig):
        """CGI directory routes are added."""
        server = GopherServer(config_with_cgi)

        # Find cgi-bin route
        patterns = [route.pattern for route in server.router.routes]
        assert "/cgi-bin/" in patterns

    def test_cgi_routes_are_prefix(self, config_with_cgi: ServerConfig):
        """CGI routes use prefix matching."""
        server = GopherServer(config_with_cgi)

        # Find cgi-bin route
        cgi_routes = [r for r in server.router.routes if "cgi-bin" in r.pattern]
        for route in cgi_routes:
            assert route.route_type == RouteType.PREFIX

    def test_root_route_added(self, basic_config: ServerConfig):
        """Root route is added for static handler."""
        server = GopherServer(basic_config)

        patterns = [route.pattern for route in server.router.routes]
        assert "/" in patterns

    def test_error_handler_set(self, basic_config: ServerConfig):
        """Error handler is set for unmatched routes."""
        server = GopherServer(basic_config)

        assert server.router.default_handler is not None


class TestGopherServerStart:
    """Tests for server start."""

    async def test_start_validates_config(self, tmp_path: Path, unused_tcp_port: int):
        """Server creation validates configuration.

        Note: Validation happens during GopherServer.__init__ when
        handlers are created, not during start().
        """
        # Create config with non-existent document root
        config = ServerConfig(
            host="127.0.0.1",
            port=unused_tcp_port,
            document_root=tmp_path / "nonexistent",
        )

        # Validation happens during construction, not start
        with pytest.raises(ValueError, match="Document root does not exist"):
            GopherServer(config)

    async def test_start_creates_server(
        self, basic_config: ServerConfig, unused_tcp_port: int
    ):
        """Start creates asyncio server."""
        # Update config with available port
        basic_config.port = unused_tcp_port

        server = GopherServer(basic_config)

        try:
            await server.start()

            assert server.server is not None
            assert server.server.is_serving()
        finally:
            await server.stop()

    async def test_start_binds_to_port(
        self, basic_config: ServerConfig, unused_tcp_port: int
    ):
        """Server binds to configured port."""
        basic_config.port = unused_tcp_port

        server = GopherServer(basic_config)

        try:
            await server.start()

            # Server should be accepting connections
            sockets = server.server.sockets
            assert len(sockets) > 0

            # Check bound address
            addr = sockets[0].getsockname()
            assert addr[1] == unused_tcp_port
        finally:
            await server.stop()


class TestGopherServerStop:
    """Tests for server stop."""

    async def test_stop_closes_server(
        self, basic_config: ServerConfig, unused_tcp_port: int
    ):
        """Stop closes the server."""
        basic_config.port = unused_tcp_port

        server = GopherServer(basic_config)
        await server.start()

        await server.stop()

        assert server.server is None

    async def test_stop_when_not_started(self, basic_config: ServerConfig):
        """Stop when not started does not raise."""
        server = GopherServer(basic_config)

        # Should not raise
        await server.stop()

        assert server.server is None

    async def test_stop_idempotent(
        self, basic_config: ServerConfig, unused_tcp_port: int
    ):
        """Multiple stop calls are safe."""
        basic_config.port = unused_tcp_port

        server = GopherServer(basic_config)
        await server.start()

        # Multiple stops should be safe
        await server.stop()
        await server.stop()

        assert server.server is None


class TestGopherServerServeForever:
    """Tests for serve_forever."""

    async def test_starts_if_not_started(
        self, basic_config: ServerConfig, unused_tcp_port: int
    ):
        """serve_forever starts server if not running."""
        basic_config.port = unused_tcp_port

        server = GopherServer(basic_config)

        # Create a task that will be cancelled
        serve_task = asyncio.create_task(server.serve_forever())

        # Wait a bit for server to start
        await asyncio.sleep(0.1)

        assert server.server is not None
        assert server.server.is_serving()

        # Cancel and cleanup
        serve_task.cancel()
        try:
            await serve_task
        except asyncio.CancelledError:
            pass

        await server.stop()


class TestGopherServerIntegration:
    """Server integration tests."""

    async def test_handles_request(self, full_server):
        """Server handles incoming request."""
        port, server = full_server

        # Connect and send request
        reader, writer = await asyncio.open_connection("127.0.0.1", port)

        try:
            writer.write(b"/\r\n")
            await writer.drain()

            # Read response
            response = await reader.read(4096)

            assert len(response) > 0
            # Should end with Gopher terminator
            assert response.endswith(b".\r\n")
        finally:
            writer.close()
            await writer.wait_closed()

    async def test_serves_file(self, full_server):
        """Server serves file content."""
        port, server = full_server

        reader, writer = await asyncio.open_connection("127.0.0.1", port)

        try:
            writer.write(b"/readme.txt\r\n")
            await writer.drain()

            response = await reader.read(4096)

            assert b"test file" in response
        finally:
            writer.close()
            await writer.wait_closed()

    async def test_concurrent_requests(self, full_server):
        """Server handles concurrent requests."""
        port, server = full_server

        async def make_request():
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            try:
                writer.write(b"/readme.txt\r\n")
                await writer.drain()
                response = await reader.read(4096)
                return response
            finally:
                writer.close()
                await writer.wait_closed()

        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert b"test file" in response

    async def test_not_found_response(self, full_server):
        """Server returns error for missing files."""
        port, server = full_server

        reader, writer = await asyncio.open_connection("127.0.0.1", port)

        try:
            writer.write(b"/nonexistent.txt\r\n")
            await writer.drain()

            response = await reader.read(4096)

            # Should contain error item (type 3)
            assert b"3" in response  # Error type
            assert b"Not found" in response
        finally:
            writer.close()
            await writer.wait_closed()


class TestGopherServerCombinedHandler:
    """Tests for combined CGI/static handler."""

    async def test_cgi_by_extension(
        self, config_with_cgi: ServerConfig, unused_tcp_port: int
    ):
        """CGI scripts by extension are handled."""
        config_with_cgi.port = unused_tcp_port

        server = GopherServer(config_with_cgi)

        try:
            await server.start()

            reader, writer = await asyncio.open_connection("127.0.0.1", unused_tcp_port)

            try:
                writer.write(b"/cgi-bin/hello.cgi\r\n")
                await writer.drain()

                response = await reader.read(4096)
                assert b"Hello from CGI" in response
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await server.stop()
