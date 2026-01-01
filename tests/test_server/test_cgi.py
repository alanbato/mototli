"""Tests for CGIHandler."""

import os
import stat
from pathlib import Path

import pytest

from mototli.protocol.item_types import ItemType
from mototli.protocol.request import GopherRequest, RequestType
from mototli.server.cgi import CGIHandler


class TestCGIHandlerCreation:
    """Tests for CGIHandler initialization."""

    def test_init_with_defaults(self, cgi_document_root: Path):
        """Initialize with default extensions and directories."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        assert handler.document_root == cgi_document_root
        assert handler.hostname == "localhost"
        assert ".cgi" in handler.cgi_extensions
        assert "cgi-bin" in handler.cgi_directories

    def test_custom_extensions(self, cgi_document_root: Path):
        """Initialize with custom CGI extensions."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
            cgi_extensions=[".cgi", ".rb"],
        )

        assert handler.cgi_extensions == [".cgi", ".rb"]
        assert ".py" not in handler.cgi_extensions

    def test_custom_directories(self, cgi_document_root: Path):
        """Initialize with custom CGI directories."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
            cgi_directories=["cgi-bin", "scripts"],
        )

        assert "cgi-bin" in handler.cgi_directories
        assert "scripts" in handler.cgi_directories

    def test_custom_timeout(self, cgi_document_root: Path):
        """Initialize with custom timeout."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
            timeout=10.0,
        )

        assert handler.timeout == 10.0

    def test_default_port(self, cgi_document_root: Path):
        """Default port is 70."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        assert handler.port == 70


class TestCGIHandlerExecution:
    """Tests for CGI script execution."""

    def test_execute_simple_script(self, cgi_handler: CGIHandler):
        """Execute simple CGI script returns output."""
        request = GopherRequest(selector="/cgi-bin/hello.cgi")

        response = cgi_handler.handle(request)

        assert response.is_directory is False
        assert response.raw_body is not None
        assert b"Hello from CGI" in response.raw_body

    def test_execute_script_with_search(self, cgi_handler: CGIHandler):
        """CGI script receives search query."""
        request = GopherRequest(
            selector="/cgi-bin/echo.cgi",
            search_query="test query",
        )

        response = cgi_handler.handle(request)

        assert b"Query: test query" in response.raw_body

    def test_script_not_found(self, cgi_handler: CGIHandler):
        """Non-existent script returns error."""
        request = GopherRequest(selector="/cgi-bin/nonexistent.cgi")

        response = cgi_handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR
        assert "Not found" in response.items[0].display_text

    def test_script_not_executable(self, cgi_document_root: Path):
        """Non-executable script returns error."""
        # Create a non-executable script
        script = cgi_document_root / "cgi-bin" / "noexec.cgi"
        script.write_text("#!/bin/sh\necho 'test'\n")
        # Remove execute permission
        script.chmod(stat.S_IRUSR | stat.S_IWUSR)

        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/cgi-bin/noexec.cgi")
        response = handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR
        assert "not executable" in response.items[0].display_text.lower()

    def test_script_returns_error(self, cgi_handler: CGIHandler):
        """Script with non-zero exit returns error."""
        request = GopherRequest(selector="/cgi-bin/error.cgi")

        response = cgi_handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR
        assert "CGI error" in response.items[0].display_text

    @pytest.mark.slow
    def test_script_timeout(self, cgi_document_root: Path):
        """Long-running script times out."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
            timeout=0.5,  # Very short timeout
        )

        request = GopherRequest(selector="/cgi-bin/slow.cgi")
        response = handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR
        assert "timeout" in response.items[0].display_text.lower()

    def test_empty_selector_returns_error(self, cgi_handler: CGIHandler):
        """Empty selector returns error."""
        request = GopherRequest(selector="")

        response = cgi_handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR


class TestCGIHandlerEnvironment:
    """Tests for CGI environment variable setup."""

    def test_gateway_interface(self, cgi_handler: CGIHandler):
        """GATEWAY_INTERFACE is set correctly."""
        request = GopherRequest(selector="/cgi-bin/env.cgi")
        response = cgi_handler.handle(request)

        assert b"GATEWAY_INTERFACE=CGI/1.1" in response.raw_body

    def test_server_protocol(self, cgi_handler: CGIHandler):
        """SERVER_PROTOCOL is set to GOPHER."""
        request = GopherRequest(selector="/cgi-bin/env.cgi")
        response = cgi_handler.handle(request)

        assert b"SERVER_PROTOCOL=GOPHER" in response.raw_body

    def test_server_name(self, cgi_handler: CGIHandler):
        """SERVER_NAME is set correctly."""
        request = GopherRequest(selector="/cgi-bin/env.cgi")
        response = cgi_handler.handle(request)

        assert b"SERVER_NAME=localhost" in response.raw_body

    def test_server_port(self, cgi_handler: CGIHandler):
        """SERVER_PORT is set correctly."""
        request = GopherRequest(selector="/cgi-bin/env.cgi")
        response = cgi_handler.handle(request)

        assert b"SERVER_PORT=70" in response.raw_body

    def test_selector_variable(self, cgi_handler: CGIHandler):
        """SELECTOR environment variable is set."""
        request = GopherRequest(selector="/cgi-bin/echo.cgi")
        response = cgi_handler.handle(request)

        assert b"Selector: /cgi-bin/echo.cgi" in response.raw_body

    def test_query_string(self, cgi_handler: CGIHandler):
        """QUERY_STRING is set from search query."""
        request = GopherRequest(
            selector="/cgi-bin/echo.cgi",
            search_query="my search",
        )
        response = cgi_handler.handle(request)

        assert b"Query: my search" in response.raw_body

    def test_remote_addr(self, cgi_document_root: Path):
        """REMOTE_ADDR is set from client IP."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/cgi-bin/env.cgi")
        request.client_ip = "192.168.1.100"

        response = handler.handle(request)

        assert b"REMOTE_ADDR=192.168.1.100" in response.raw_body

    def test_gopher_plus_enabled(self, cgi_handler: CGIHandler):
        """GOPHER_PLUS is set for Gopher+ requests."""
        request = GopherRequest(
            selector="/cgi-bin/env.cgi",
            request_type=RequestType.PLUS,
        )

        response = cgi_handler.handle(request)

        assert b"GOPHER_PLUS=1" in response.raw_body

    def test_gopher_plus_disabled(self, cgi_handler: CGIHandler):
        """GOPHER_PLUS is 0 for standard requests."""
        request = GopherRequest(selector="/cgi-bin/env.cgi")

        response = cgi_handler.handle(request)

        assert b"GOPHER_PLUS=0" in response.raw_body

    def test_request_type_variable(self, cgi_handler: CGIHandler):
        """REQUEST_TYPE is set for Gopher+ requests."""
        request = GopherRequest(
            selector="/cgi-bin/env.cgi",
            request_type=RequestType.ATTRIBUTES,
        )

        response = cgi_handler.handle(request)

        assert b"REQUEST_TYPE=!" in response.raw_body

    def test_script_name(self, cgi_handler: CGIHandler):
        """SCRIPT_NAME is set correctly."""
        request = GopherRequest(selector="/cgi-bin/env.cgi")
        response = cgi_handler.handle(request)

        assert b"SCRIPT_NAME=" in response.raw_body


class TestCGIHandlerOutput:
    """Tests for CGI output parsing."""

    def test_parse_text_output(self, cgi_handler: CGIHandler):
        """Plain text output is returned as raw body."""
        request = GopherRequest(selector="/cgi-bin/hello.cgi")

        response = cgi_handler.handle(request)

        assert response.is_directory is False
        assert response.raw_body is not None

    def test_parse_directory_output(self, cgi_handler: CGIHandler):
        """Directory-style output is parsed as items."""
        request = GopherRequest(selector="/cgi-bin/dir.cgi")

        response = cgi_handler.handle(request)

        assert response.is_directory is True
        assert len(response.items) > 0

        # Check that items were parsed correctly
        types = [item.item_type for item in response.items]
        assert ItemType.INFO in types  # "Generated directory listing"
        assert ItemType.TEXT in types  # "Item One"
        assert ItemType.DIRECTORY in types  # "Item Two"


class TestCGIHandlerDetection:
    """Tests for CGI script detection."""

    def test_detect_by_extension(self, cgi_handler: CGIHandler):
        """Detect CGI by file extension."""
        assert cgi_handler.can_handle("/scripts/test.py") is True
        assert cgi_handler.can_handle("/scripts/test.cgi") is True

    @pytest.mark.parametrize("ext", [".cgi", ".py"])
    def test_default_extensions(self, cgi_handler: CGIHandler, ext: str):
        """Default CGI extensions are recognized."""
        assert cgi_handler.can_handle(f"/path/script{ext}") is True

    def test_detect_by_directory(self, cgi_handler: CGIHandler):
        """Detect CGI by cgi-bin directory."""
        assert cgi_handler.can_handle("/cgi-bin/anything") is True
        assert cgi_handler.can_handle("/cgi-bin/script.txt") is True

    def test_can_handle_method(self, cgi_handler: CGIHandler):
        """can_handle() correctly identifies CGI selectors."""
        # Should handle
        assert cgi_handler.can_handle("/cgi-bin/script") is True
        assert cgi_handler.can_handle("/path/script.cgi") is True
        assert cgi_handler.can_handle("/path/script.py") is True

        # Should not handle
        assert cgi_handler.can_handle("/path/file.txt") is False
        assert cgi_handler.can_handle("/other/script") is False

    def test_non_cgi_file_in_cgi_directory(self, cgi_document_root: Path):
        """Non-CGI file in CGI directory can still be handled."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        # cgi-bin directory makes it "handleable"
        assert handler.can_handle("/cgi-bin/readme.txt") is True


class TestCGIHandlerSecurity:
    """Tests for CGI security measures."""

    def test_path_traversal_blocked(self, cgi_handler: CGIHandler):
        """Path traversal in CGI requests is blocked."""
        request = GopherRequest(selector="/cgi-bin/../../../etc/passwd")

        response = cgi_handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR

    def test_only_executable_files(self, cgi_document_root: Path):
        """Only executable files can be run as CGI."""
        # Create a non-executable file in cgi-bin
        text_file = cgi_document_root / "cgi-bin" / "readme.txt"
        text_file.write_text("This is not a script")

        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/cgi-bin/readme.txt")
        response = handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR

    def test_script_must_be_cgi(self, cgi_document_root: Path):
        """Non-CGI files cannot be executed even if executable."""
        # Create an executable file outside cgi-bin without CGI extension
        script = cgi_document_root / "script"
        script.write_text("#!/bin/sh\necho 'test'\n")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)

        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/script")
        response = handler.handle(request)

        # Should fail because it's not in cgi-bin and doesn't have CGI extension
        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR


class TestCGIHandlerAsync:
    """Tests for async CGI execution."""

    async def test_async_execution(self, cgi_handler: CGIHandler):
        """Async CGI execution works correctly."""
        script_path = cgi_handler.document_root / "cgi-bin" / "hello.cgi"
        request = GopherRequest(selector="/cgi-bin/hello.cgi")

        response = await cgi_handler.execute_cgi_async(script_path, request)

        assert response.is_directory is False
        assert b"Hello from CGI" in response.raw_body

    @pytest.mark.slow
    async def test_async_timeout(self, cgi_document_root: Path):
        """Async CGI respects timeout."""
        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
            timeout=0.5,
        )

        script_path = cgi_document_root / "cgi-bin" / "slow.cgi"
        request = GopherRequest(selector="/cgi-bin/slow.cgi")

        response = await handler.execute_cgi_async(script_path, request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR
        assert "timeout" in response.items[0].display_text.lower()


class TestCGIHandlerEdgeCases:
    """Edge case tests for CGIHandler."""

    def test_directory_instead_of_file(self, cgi_handler: CGIHandler):
        """Requesting a directory returns error."""
        request = GopherRequest(selector="/cgi-bin")

        response = cgi_handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR

    def test_binary_output(self, cgi_document_root: Path):
        """CGI script can output binary data."""
        # Create a script that outputs binary
        script = cgi_document_root / "cgi-bin" / "binary.cgi"
        script.write_text('#!/bin/sh\nprintf "\\x00\\x01\\x02\\xff"\n')
        script.chmod(script.stat().st_mode | stat.S_IXUSR)

        handler = CGIHandler(
            document_root=cgi_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/cgi-bin/binary.cgi")
        response = handler.handle(request)

        assert response.is_directory is False
        # Binary data should be preserved
        assert response.raw_body is not None
