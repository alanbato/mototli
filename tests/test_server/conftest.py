"""Shared fixtures for server tests."""

import asyncio
import os
import stat
from pathlib import Path
from unittest.mock import Mock

import pytest

from mototli.protocol.request import GopherRequest, RequestType
from mototli.server.cgi import CGIHandler
from mototli.server.config import ServerConfig
from mototli.server.handler import ErrorHandler, StaticFileHandler
from mototli.server.protocol import GopherServerProtocol
from mototli.server.router import Router, RouteType

# =============================================================================
# Document Root Fixtures
# =============================================================================


@pytest.fixture
def document_root(tmp_path: Path) -> Path:
    """Create an empty temporary document root."""
    return tmp_path


@pytest.fixture
def populated_document_root(tmp_path: Path) -> Path:
    """Create a document root populated with test files.

    Structure:
        index.gph           - gophermap index
        readme.txt          - text file
        binary.bin          - binary file
        subdir/             - subdirectory
            file.txt        - nested text file
            nested/         - nested directory
                deep.txt    - deeply nested file
        images/             - image directory
            test.gif        - GIF file (fake, just has extension)
    """
    # Create index gophermap
    gophermap = tmp_path / "index.gph"
    gophermap.write_text(
        "iWelcome to the test server!\t\tnull.host\t0\n"
        "1Subdirectory\t/subdir\tlocalhost\t70\n"
        "0Readme\t/readme.txt\tlocalhost\t70\n"
    )

    # Create text file
    readme = tmp_path / "readme.txt"
    readme.write_text("This is a test file.\nWith multiple lines.\n")

    # Create binary file
    binary = tmp_path / "binary.bin"
    binary.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

    # Create subdirectory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("Nested file content")
    (subdir / "gophermap").write_text(
        "iSubdirectory index\t\tnull.host\t0\n0File\t/subdir/file.txt\tlocalhost\t70\n"
    )

    # Create nested directory
    nested = subdir / "nested"
    nested.mkdir()
    (nested / "deep.txt").write_text("Deep content")

    # Create images directory
    images = tmp_path / "images"
    images.mkdir()
    (images / "test.gif").write_bytes(b"GIF89a")  # Minimal GIF header

    return tmp_path


@pytest.fixture
def cgi_document_root(tmp_path: Path) -> Path:
    """Create a document root with CGI scripts.

    Structure:
        cgi-bin/            - CGI directory
            hello.cgi       - Simple hello script
            echo.cgi        - Script that echoes SELECTOR
            env.cgi         - Script that prints environment
            slow.cgi        - Script that takes time
            error.cgi       - Script that returns error
            dir.cgi         - Script that outputs directory format
        scripts/            - Another directory
            test.py         - Python CGI script (by extension)
    """
    # Create cgi-bin directory
    cgi_bin = tmp_path / "cgi-bin"
    cgi_bin.mkdir()

    # Simple hello script
    hello = cgi_bin / "hello.cgi"
    hello.write_text("#!/bin/sh\necho 'Hello from CGI!'\n")
    hello.chmod(hello.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Echo selector script
    echo = cgi_bin / "echo.cgi"
    echo.write_text(
        '#!/bin/sh\necho "Selector: $SELECTOR"\necho "Query: $QUERY_STRING"\n'
    )
    echo.chmod(echo.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Environment script
    env_script = cgi_bin / "env.cgi"
    env_script.write_text("#!/bin/sh\nenv | sort\n")
    env_script.chmod(
        env_script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )

    # Slow script (for timeout testing)
    slow = cgi_bin / "slow.cgi"
    slow.write_text("#!/bin/sh\nsleep 5\necho 'Done'\n")
    slow.chmod(slow.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Error script
    error = cgi_bin / "error.cgi"
    error.write_text("#!/bin/sh\nexit 1\n")
    error.chmod(error.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Directory output script
    dir_script = cgi_bin / "dir.cgi"
    dir_script.write_text(
        "#!/bin/sh\n"
        'echo "iGenerated directory listing\t\tnull.host\t0"\n'
        'echo "0Item One\t/item1\tlocalhost\t70"\n'
        'echo "1Item Two\t/item2\tlocalhost\t70"\n'
    )
    dir_script.chmod(
        dir_script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )

    # Create scripts directory with Python script
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    py_script = scripts / "test.py"
    py_script.write_text("#!/usr/bin/env python3\nprint('Hello from Python')\n")
    py_script.chmod(py_script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return tmp_path


@pytest.fixture
def gophermap_content() -> str:
    """Sample gophermap content for parsing tests."""
    return (
        "iWelcome to the Gopher server\t\tnull.host\t0\n"
        "i\t\tnull.host\t0\n"
        "1Main Directory\t/\tlocalhost\t70\n"
        "0About\t/about.txt\tlocalhost\t70\n"
        "1Remote Link\t/\tother.host\t7070\n"
        "7Search\t/search\tlocalhost\t70\n"
        "hWeb Link\tURL:https://example.com\tlocalhost\t70\n"
    )


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def basic_config(populated_document_root: Path) -> ServerConfig:
    """Basic server configuration for testing."""
    return ServerConfig(
        host="127.0.0.1",
        port=7070,
        document_root=populated_document_root,
        hostname="localhost",
        gopher_plus=False,
    )


@pytest.fixture
def gopher_plus_config(populated_document_root: Path) -> ServerConfig:
    """Configuration with Gopher+ enabled and admin info."""
    return ServerConfig(
        host="127.0.0.1",
        port=7070,
        document_root=populated_document_root,
        hostname="localhost",
        gopher_plus=True,
        admin_name="Test Admin",
        admin_email="admin@test.com",
    )


@pytest.fixture
def config_with_cgi(cgi_document_root: Path) -> ServerConfig:
    """Configuration with CGI enabled."""
    return ServerConfig(
        host="127.0.0.1",
        port=7070,
        document_root=cgi_document_root,
        hostname="localhost",
        cgi_extensions=[".cgi", ".py"],
        cgi_directories=["cgi-bin"],
        cgi_timeout=2.0,  # Short timeout for tests
    )


@pytest.fixture
def restricted_config(populated_document_root: Path) -> ServerConfig:
    """Configuration with directory listing disabled."""
    return ServerConfig(
        host="127.0.0.1",
        port=7070,
        document_root=populated_document_root,
        hostname="localhost",
        enable_directory_listing=False,
    )


# =============================================================================
# Handler Fixtures
# =============================================================================


@pytest.fixture
def static_handler(populated_document_root: Path) -> StaticFileHandler:
    """Pre-configured static file handler."""
    return StaticFileHandler(
        document_root=populated_document_root,
        hostname="localhost",
        port=70,
        gopher_plus=True,
        admin_name="Test Admin",
        admin_email="admin@test.com",
    )


@pytest.fixture
def cgi_handler(cgi_document_root: Path) -> CGIHandler:
    """Pre-configured CGI handler."""
    return CGIHandler(
        document_root=cgi_document_root,
        hostname="localhost",
        port=70,
        cgi_extensions=[".cgi", ".py"],
        cgi_directories=["cgi-bin"],
        timeout=2.0,
    )


@pytest.fixture
def error_handler() -> ErrorHandler:
    """Pre-configured error handler."""
    return ErrorHandler("Not found")


# =============================================================================
# Router Fixtures
# =============================================================================


@pytest.fixture
def basic_router(static_handler: StaticFileHandler) -> Router:
    """Router with basic static file routes."""
    router = Router()
    router.add_route("/", static_handler.handle, RouteType.PREFIX)
    return router


@pytest.fixture
def router_with_cgi(static_handler: StaticFileHandler, cgi_handler: CGIHandler) -> Router:
    """Router with both static and CGI routes."""
    router = Router()
    router.add_route("/cgi-bin/", cgi_handler.handle, RouteType.PREFIX)
    router.add_route("/", static_handler.handle, RouteType.PREFIX)
    return router


# =============================================================================
# Protocol Fixtures
# =============================================================================


@pytest.fixture
def mock_transport(mocker) -> Mock:
    """Mock asyncio.Transport for protocol testing."""
    transport = mocker.Mock()
    transport.get_extra_info.return_value = ("127.0.0.1", 12345)
    transport.is_closing.return_value = False
    return transport


@pytest.fixture
def protocol_with_handler(basic_router: Router) -> GopherServerProtocol:
    """Protocol instance with router-based handler."""
    return GopherServerProtocol(
        request_handler=basic_router.route,
        request_timeout=5.0,
    )


# =============================================================================
# Server Fixtures (Two-Tier Approach)
# =============================================================================


@pytest.fixture
async def lightweight_server(unused_tcp_port: int, populated_document_root: Path):
    """Lightweight server using GopherServerProtocol directly.

    Fast startup/teardown for basic integration tests.
    Uses minimal setup without full GopherServer lifecycle.

    Yields:
        The port number the server is listening on.
    """
    router = Router()
    handler = StaticFileHandler(
        document_root=populated_document_root,
        hostname="localhost",
        port=unused_tcp_port,
        gopher_plus=True,
    )
    router.set_default_handler(handler.handle)

    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        lambda: GopherServerProtocol(router.route),
        "127.0.0.1",
        unused_tcp_port,
    )

    await asyncio.sleep(0.1)  # Small delay for server to start
    yield unused_tcp_port

    server.close()
    await server.wait_closed()


@pytest.fixture
async def lightweight_cgi_server(unused_tcp_port: int, cgi_document_root: Path):
    """Lightweight server with CGI support.

    Yields:
        The port number the server is listening on.
    """
    router = Router()

    cgi_handler = CGIHandler(
        document_root=cgi_document_root,
        hostname="localhost",
        port=unused_tcp_port,
        timeout=2.0,
    )
    static_handler = StaticFileHandler(
        document_root=cgi_document_root,
        hostname="localhost",
        port=unused_tcp_port,
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


@pytest.fixture
async def full_server(unused_tcp_port: int, populated_document_root: Path):
    """Full production server with GopherServer class.

    Uses the production start() method with complete configuration.
    Suitable for testing lifecycle management and all features.

    Yields:
        Tuple of (port, server) where server is the GopherServer instance.
    """
    from mototli.server import GopherServer

    config = ServerConfig(
        host="127.0.0.1",
        port=unused_tcp_port,
        document_root=populated_document_root,
        hostname="localhost",
        gopher_plus=True,
        admin_name="Test Admin",
        admin_email="admin@test.com",
    )

    server = GopherServer(config)
    await server.start()

    yield unused_tcp_port, server

    await server.stop()


# =============================================================================
# Request Fixtures
# =============================================================================


@pytest.fixture
def root_request() -> GopherRequest:
    """Request for root selector."""
    return GopherRequest(selector="/")


@pytest.fixture
def file_request() -> GopherRequest:
    """Request for a specific file."""
    return GopherRequest(selector="/readme.txt")


@pytest.fixture
def directory_request() -> GopherRequest:
    """Request for a directory."""
    return GopherRequest(selector="/subdir")


@pytest.fixture
def gopher_plus_request() -> GopherRequest:
    """Gopher+ request with + modifier."""
    return GopherRequest(selector="/readme.txt", request_type=RequestType.PLUS)


@pytest.fixture
def attributes_request() -> GopherRequest:
    """Gopher+ attributes-only request with ! modifier."""
    return GopherRequest(selector="/readme.txt", request_type=RequestType.ATTRIBUTES)


@pytest.fixture
def directory_attributes_request() -> GopherRequest:
    """Gopher+ directory attributes request with $ modifier."""
    return GopherRequest(selector="/subdir", request_type=RequestType.DIRECTORY)


@pytest.fixture
def search_request() -> GopherRequest:
    """Request with search query."""
    return GopherRequest(selector="/search", search_query="test query")
