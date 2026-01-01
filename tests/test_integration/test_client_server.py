"""Integration tests for Gopher client-server interaction."""

import asyncio
import os
import stat
from pathlib import Path

import pytest

from mototli.client import GopherClient
from mototli.protocol.item_types import ItemType
from mototli.protocol.request import RequestType
from mototli.server import GopherServer
from mototli.server.cgi import CGIHandler
from mototli.server.config import ServerConfig
from mototli.server.handler import StaticFileHandler
from mototli.server.protocol import GopherServerProtocol
from mototli.server.router import Router, RouteType


def create_test_gopher_hole(path: Path) -> None:
    """Create a standard test gopher hole directory with content.

    Structure:
        index.gph           - gophermap index
        about.txt           - about page
        files/              - file directory
            readme.txt      - readme file
            data.bin        - binary file
        cgi-bin/            - CGI scripts
            hello.cgi       - simple hello script
            search.cgi      - search script
    """
    # Create gophermap index
    gophermap = path / "index.gph"
    gophermap.write_text(
        "iWelcome to the Test Gopher Hole!\t\tnull.host\t0\n"
        "i\t\tnull.host\t0\n"
        "iThis is a test server for integration testing.\t\tnull.host\t0\n"
        "i\t\tnull.host\t0\n"
        "0About\t/about.txt\tlocalhost\t70\n"
        "1Files\t/files\tlocalhost\t70\n"
        "1CGI Scripts\t/cgi-bin\tlocalhost\t70\n"
    )

    # Create about page
    about = path / "about.txt"
    about.write_text("About this Gopher Hole\n\nThis is a test server.\n")

    # Create files directory
    files_dir = path / "files"
    files_dir.mkdir()
    (files_dir / "readme.txt").write_text("This is a readme file.")
    (files_dir / "data.bin").write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
    (files_dir / "gophermap").write_text(
        "iFile Directory\t\tnull.host\t0\n"
        "0Readme\t/files/readme.txt\tlocalhost\t70\n"
        "9Binary Data\t/files/data.bin\tlocalhost\t70\n"
    )

    # Create cgi-bin directory
    cgi_bin = path / "cgi-bin"
    cgi_bin.mkdir()

    hello = cgi_bin / "hello.cgi"
    hello.write_text("#!/bin/sh\necho 'Hello from CGI!'\n")
    hello.chmod(hello.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    search = cgi_bin / "search.cgi"
    search.write_text(
        "#!/bin/sh\n"
        'echo "iSearch Results for: $QUERY_STRING\t\tnull.host\t0"\n'
        'echo "0Result 1\t/result1\tlocalhost\t70"\n'
        'echo "0Result 2\t/result2\tlocalhost\t70"\n'
    )
    search.chmod(search.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture
def test_gopher_hole(tmp_path: Path) -> Path:
    """Create a test gopher hole and return its path."""
    create_test_gopher_hole(tmp_path)
    return tmp_path


@pytest.fixture
async def integration_server(unused_tcp_port: int, test_gopher_hole: Path):
    """Start an integration test server.

    Yields:
        Tuple of (port, server) for the running server.
    """
    config = ServerConfig(
        host="127.0.0.1",
        port=unused_tcp_port,
        document_root=test_gopher_hole,
        hostname="localhost",
        gopher_plus=True,
        admin_name="Test Admin",
        admin_email="admin@test.local",
        cgi_timeout=2.0,
    )

    server = GopherServer(config)
    await server.start()

    yield unused_tcp_port, server

    await server.stop()


@pytest.fixture
async def lightweight_integration_server(unused_tcp_port: int, test_gopher_hole: Path):
    """Start a lightweight integration test server.

    Uses GopherServerProtocol directly for faster startup.

    Yields:
        The port number the server is listening on.
    """
    router = Router()

    cgi_handler = CGIHandler(
        document_root=test_gopher_hole,
        hostname="localhost",
        port=unused_tcp_port,
        timeout=2.0,
    )
    static_handler = StaticFileHandler(
        document_root=test_gopher_hole,
        hostname="localhost",
        port=unused_tcp_port,
        gopher_plus=True,
    )

    router.add_route("/cgi-bin/", cgi_handler.handle, RouteType.PREFIX)
    router.set_default_handler(static_handler.handle)

    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        lambda: GopherServerProtocol(router.route),
        "127.0.0.1",
        unused_tcp_port,
    )

    await asyncio.sleep(0.1)
    yield unused_tcp_port

    server.close()
    await server.wait_closed()


@pytest.mark.integration
@pytest.mark.network
class TestBasicRequests:
    """Basic client-server integration tests."""

    async def test_get_root_directory(self, lightweight_integration_server: int):
        """Get root directory listing."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/",
            )

        assert response.is_directory is True
        assert len(response.items) > 0

        # Check for expected content
        texts = [item.display_text for item in response.items]
        assert any("Welcome" in t for t in texts)
        assert any("About" in t for t in texts)

    async def test_get_text_file(self, lightweight_integration_server: int):
        """Get text file content."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/about.txt",
                item_type=ItemType.TEXT,  # Specify text type for proper parsing
            )

        assert response.is_directory is False
        assert response.raw_body is not None
        assert b"About this Gopher Hole" in response.raw_body

    async def test_get_binary_file(self, lightweight_integration_server: int):
        """Get binary file content."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/files/data.bin",
                item_type=ItemType.BINARY,  # Specify binary type
            )

        assert response.is_directory is False
        assert response.raw_body == b"\x00\x01\x02\x03\xff\xfe\xfd"

    async def test_get_not_found(self, lightweight_integration_server: int):
        """Get non-existent resource returns error."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/nonexistent.txt",
            )

        assert response.is_directory is True
        assert len(response.items) > 0
        assert response.items[0].item_type == ItemType.ERROR

    async def test_get_subdirectory(self, lightweight_integration_server: int):
        """Get subdirectory listing."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/files",
            )

        assert response.is_directory is True
        assert len(response.items) > 0

        # Should have readme and binary file entries
        texts = [item.display_text for item in response.items]
        assert any("Readme" in t for t in texts)


@pytest.mark.integration
@pytest.mark.network
class TestGopherPlusIntegration:
    """Gopher+ integration tests."""

    async def test_gopher_plus_attributes_request(self, integration_server):
        """Gopher+ attributes request returns attributes."""
        port, server = integration_server

        async with GopherClient(timeout=5.0) as client:
            attrs = await client.get_attributes(
                host="127.0.0.1",
                port=port,
                selector="/about.txt",
            )

        # Should return GopherAttributes object
        assert attrs is not None
        assert attrs.info is not None

    async def test_get_attributes_has_info(self, integration_server):
        """Get attributes includes +INFO block."""
        port, server = integration_server

        async with GopherClient(timeout=5.0) as client:
            attrs = await client.get_attributes(
                host="127.0.0.1",
                port=port,
                selector="/about.txt",
            )

        assert attrs.info is not None
        # INFO should have the correct display text
        assert "about.txt" in attrs.info.display_text


@pytest.mark.integration
@pytest.mark.network
class TestCGIIntegration:
    """CGI integration tests."""

    async def test_execute_cgi_script(self, lightweight_integration_server: int):
        """Execute CGI script via request."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/cgi-bin/hello.cgi",
                item_type=ItemType.TEXT,  # CGI outputs text
            )

        # The CGI script outputs plain text
        assert response.raw_body is not None
        assert b"Hello from CGI" in response.raw_body

    async def test_cgi_with_search_query(self, lightweight_integration_server: int):
        """CGI script receives search query."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/cgi-bin/search.cgi",
                search_query="python programming",  # Use search_query, not search
            )

        # This CGI outputs directory-style content
        assert response.is_directory is True
        texts = [item.display_text for item in response.items]
        assert any("python programming" in t for t in texts)


@pytest.mark.integration
@pytest.mark.network
class TestGophermapIntegration:
    """Gophermap integration tests."""

    async def test_serve_gophermap(self, lightweight_integration_server: int):
        """Gophermap file is parsed and served."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/",
            )

        assert response.is_directory is True

        # Check item types
        types = [item.item_type for item in response.items]
        assert ItemType.INFO in types
        assert ItemType.TEXT in types
        assert ItemType.DIRECTORY in types

    async def test_gophermap_links(self, lightweight_integration_server: int):
        """Gophermap links are correct."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/",
            )

        # Find the About link
        about_items = [i for i in response.items if "About" in i.display_text]
        assert len(about_items) > 0

        about_item = about_items[0]
        assert about_item.selector == "/about.txt"
        assert about_item.item_type == ItemType.TEXT


@pytest.mark.integration
@pytest.mark.network
class TestErrorHandling:
    """Error handling integration tests."""

    async def test_path_traversal_blocked(self, lightweight_integration_server: int):
        """Path traversal attempts are blocked."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=port,
                selector="/../../../etc/passwd",
            )

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR

    async def test_connection_refused(self, unused_tcp_port: int):
        """Connection to non-running server fails gracefully."""
        async with GopherClient(timeout=2.0) as client:
            with pytest.raises((ConnectionRefusedError, OSError)):
                await client.get(
                    host="127.0.0.1",
                    port=unused_tcp_port,  # Nothing listening
                    selector="/",
                )


@pytest.mark.integration
@pytest.mark.network
class TestConcurrency:
    """Concurrency integration tests."""

    async def test_multiple_sequential_requests(
        self, lightweight_integration_server: int
    ):
        """Multiple sequential requests work correctly."""
        port = lightweight_integration_server

        async with GopherClient(timeout=5.0) as client:
            # Make multiple requests sequentially
            for _ in range(5):
                response = await client.get(
                    host="127.0.0.1",
                    port=port,
                    selector="/about.txt",
                    item_type=ItemType.TEXT,
                )
                assert b"About this Gopher Hole" in response.raw_body

    async def test_concurrent_requests(self, lightweight_integration_server: int):
        """Concurrent requests are handled correctly."""
        port = lightweight_integration_server

        async def make_request():
            async with GopherClient(timeout=5.0) as client:
                response = await client.get(
                    host="127.0.0.1",
                    port=port,
                    selector="/about.txt",
                    item_type=ItemType.TEXT,
                )
                return response

        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.is_directory is False
            assert b"About this Gopher Hole" in response.raw_body


@pytest.mark.integration
@pytest.mark.network
class TestServerLifecycle:
    """Server lifecycle integration tests."""

    async def test_server_start_stop(self, unused_tcp_port: int, test_gopher_hole: Path):
        """Server can be started and stopped cleanly."""
        config = ServerConfig(
            host="127.0.0.1",
            port=unused_tcp_port,
            document_root=test_gopher_hole,
        )

        server = GopherServer(config)

        # Start
        await server.start()
        assert server.server is not None
        assert server.server.is_serving()

        # Verify it works
        async with GopherClient(timeout=5.0) as client:
            response = await client.get(
                host="127.0.0.1",
                port=unused_tcp_port,
                selector="/",
            )
            assert response.is_directory is True

        # Stop
        await server.stop()
        assert server.server is None

    async def test_requests_during_shutdown(
        self, unused_tcp_port: int, test_gopher_hole: Path
    ):
        """Pending requests complete during graceful shutdown."""
        config = ServerConfig(
            host="127.0.0.1",
            port=unused_tcp_port,
            document_root=test_gopher_hole,
        )

        server = GopherServer(config)
        await server.start()

        # Start a request
        async with GopherClient(timeout=5.0) as client:
            response_task = asyncio.create_task(
                client.get(
                    host="127.0.0.1",
                    port=unused_tcp_port,
                    selector="/about.txt",
                    item_type=ItemType.TEXT,
                )
            )

            # Wait a bit for request to start
            await asyncio.sleep(0.05)

            # Request should complete
            response = await response_task
            assert b"About" in response.raw_body

        await server.stop()
