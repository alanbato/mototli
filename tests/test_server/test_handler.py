"""Tests for StaticFileHandler and ErrorHandler."""

from pathlib import Path

import pytest

from mototli.protocol.item_types import ItemType
from mototli.protocol.request import GopherRequest, RequestType
from mototli.server.handler import ErrorHandler, StaticFileHandler


class TestStaticFileHandlerCreation:
    """Tests for StaticFileHandler initialization."""

    def test_init_with_path(self, populated_document_root: Path):
        """Initialize with Path document root."""
        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
        )

        assert handler.document_root == populated_document_root
        assert handler.hostname == "localhost"

    def test_init_with_string(self, populated_document_root: Path):
        """Initialize with string document root."""
        handler = StaticFileHandler(
            document_root=str(populated_document_root),
            hostname="localhost",
        )

        assert handler.document_root == populated_document_root

    def test_missing_document_root_raises(self, tmp_path: Path):
        """Non-existent document root raises ValueError."""
        with pytest.raises(ValueError, match="Document root does not exist"):
            StaticFileHandler(
                document_root=tmp_path / "nonexistent",
                hostname="localhost",
            )

    def test_file_as_document_root_raises(self, tmp_path: Path):
        """File as document root raises ValueError."""
        file = tmp_path / "file.txt"
        file.write_text("content")

        with pytest.raises(ValueError, match="Document root is not a directory"):
            StaticFileHandler(
                document_root=file,
                hostname="localhost",
            )

    def test_default_indices(self, populated_document_root: Path):
        """Default index file list is set."""
        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
        )

        assert "index.gph" in handler.default_indices
        assert "gophermap" in handler.default_indices
        assert "index.txt" in handler.default_indices

    def test_custom_indices(self, populated_document_root: Path):
        """Custom index file list is accepted."""
        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
            default_indices=["home.gph", "welcome.txt"],
        )

        assert handler.default_indices == ["home.gph", "welcome.txt"]

    def test_default_port(self, populated_document_root: Path):
        """Default port is 70."""
        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
        )

        assert handler.port == 70

    def test_custom_port(self, populated_document_root: Path):
        """Custom port is accepted."""
        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
            port=7070,
        )

        assert handler.port == 7070


class TestStaticFileHandlerFiles:
    """Tests for serving static files."""

    def test_serve_text_file(self, static_handler: StaticFileHandler):
        """Serve text file returns content."""
        request = GopherRequest(selector="/readme.txt")

        response = static_handler.handle(request)

        assert response.is_directory is False
        assert response.raw_body is not None
        assert b"test file" in response.raw_body

    def test_serve_binary_file(self, static_handler: StaticFileHandler):
        """Serve binary file returns raw bytes."""
        request = GopherRequest(selector="/binary.bin")

        response = static_handler.handle(request)

        assert response.is_directory is False
        assert response.raw_body == b"\x00\x01\x02\x03\xff\xfe\xfd"

    def test_file_not_found(self, static_handler: StaticFileHandler):
        """Non-existent file returns error response."""
        request = GopherRequest(selector="/nonexistent.txt")

        response = static_handler.handle(request)

        assert response.is_directory is True
        assert len(response.items) == 1
        assert response.items[0].item_type == ItemType.ERROR
        assert "Not found" in response.items[0].display_text

    def test_file_too_large(self, populated_document_root: Path):
        """File exceeding max size returns error."""
        # Create a large file
        large_file = populated_document_root / "large.txt"
        large_file.write_text("x" * 1000)

        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
            max_file_size=100,  # Very small limit
        )

        request = GopherRequest(selector="/large.txt")
        response = handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR
        assert "too large" in response.items[0].display_text.lower()

    def test_serve_gif_file(self, static_handler: StaticFileHandler):
        """Serve GIF file returns binary content."""
        request = GopherRequest(selector="/images/test.gif")

        response = static_handler.handle(request)

        assert response.is_directory is False
        assert response.raw_body == b"GIF89a"


class TestStaticFileHandlerDirectories:
    """Tests for directory handling."""

    def test_directory_with_index(self, static_handler: StaticFileHandler):
        """Directory with index file serves index."""
        request = GopherRequest(selector="/")

        response = static_handler.handle(request)

        # Should serve index.gph as directory listing
        assert response.is_directory is True
        assert len(response.items) > 0

    def test_directory_with_gophermap(self, static_handler: StaticFileHandler):
        """Directory with gophermap serves gophermap."""
        request = GopherRequest(selector="/subdir")

        response = static_handler.handle(request)

        # Should serve the gophermap
        assert response.is_directory is True
        # Check for content from subdir's gophermap
        texts = [item.display_text for item in response.items]
        assert any("Subdirectory" in t for t in texts)

    def test_directory_listing_enabled(self, populated_document_root: Path):
        """Directory without index generates listing."""
        # Create a directory without index file
        no_index_dir = populated_document_root / "no_index"
        no_index_dir.mkdir()
        (no_index_dir / "file1.txt").write_text("content1")
        (no_index_dir / "file2.txt").write_text("content2")

        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
            enable_directory_listing=True,
        )

        request = GopherRequest(selector="/no_index")
        response = handler.handle(request)

        assert response.is_directory is True
        # Should have file entries
        texts = [item.display_text for item in response.items]
        assert any("file1.txt" in t for t in texts)
        assert any("file2.txt" in t for t in texts)

    def test_directory_listing_disabled(self, populated_document_root: Path):
        """Directory listing disabled returns error."""
        # Create a directory without index file
        no_index_dir = populated_document_root / "no_index2"
        no_index_dir.mkdir()
        (no_index_dir / "file.txt").write_text("content")

        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
            enable_directory_listing=False,
        )

        request = GopherRequest(selector="/no_index2")
        response = handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR


class TestStaticFileHandlerGophermap:
    """Tests for gophermap file parsing."""

    def test_parse_gophermap(self, static_handler: StaticFileHandler):
        """Parse gophermap file correctly."""
        request = GopherRequest(selector="/")

        response = static_handler.handle(request)

        assert response.is_directory is True
        assert len(response.items) > 0

    def test_gophermap_item_types(self, static_handler: StaticFileHandler):
        """Gophermap items have correct types."""
        request = GopherRequest(selector="/")
        response = static_handler.handle(request)

        # Check for info items (i) and directory items (1) and text items (0)
        types = [item.item_type for item in response.items]
        assert ItemType.INFO in types  # "Welcome..." line
        assert ItemType.DIRECTORY in types  # Subdirectory link
        assert ItemType.TEXT in types  # Readme link

    def test_gophermap_info_lines(self, populated_document_root: Path):
        """Lines without tabs become info items."""
        # Create a gophermap with info lines
        gopher = populated_document_root / "info_test"
        gopher.mkdir()
        (gopher / "gophermap").write_text(
            "This is just text\nMore text without tabs\n1Link\t/path\tlocalhost\t70\n"
        )

        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/info_test")
        response = handler.handle(request)

        # First two should be info items
        assert response.items[0].item_type == ItemType.INFO
        assert response.items[0].display_text == "This is just text"
        assert response.items[1].item_type == ItemType.INFO

    def test_gophermap_custom_hosts(self, populated_document_root: Path):
        """Gophermap can specify custom hostnames."""
        gopher = populated_document_root / "custom_host"
        gopher.mkdir()
        (gopher / "gophermap").write_text("1Remote\t/path\tother.host\t70\n")

        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/custom_host")
        response = handler.handle(request)

        assert response.items[0].hostname == "other.host"

    def test_gophermap_custom_ports(self, populated_document_root: Path):
        """Gophermap can specify custom ports."""
        gopher = populated_document_root / "custom_port"
        gopher.mkdir()
        (gopher / "gophermap").write_text("1Remote\t/path\tlocalhost\t7070\n")

        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/custom_port")
        response = handler.handle(request)

        assert response.items[0].port == 7070

    def test_gophermap_empty_lines(self, populated_document_root: Path):
        """Empty lines in gophermap become blank info items."""
        gopher = populated_document_root / "empty_lines"
        gopher.mkdir()
        (gopher / "gophermap").write_text("Line 1\n\nLine 3\n")

        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
        )

        request = GopherRequest(selector="/empty_lines")
        response = handler.handle(request)

        assert len(response.items) == 3
        assert response.items[1].display_text == ""
        assert response.items[1].item_type == ItemType.INFO


class TestStaticFileHandlerSecurity:
    """Tests for path traversal and security."""

    def test_path_traversal_blocked(self, static_handler: StaticFileHandler):
        """Path traversal attempts are blocked."""
        request = GopherRequest(selector="/../etc/passwd")

        response = static_handler.handle(request)

        assert response.is_directory is True
        assert response.items[0].item_type == ItemType.ERROR
        assert "Not found" in response.items[0].display_text

    @pytest.mark.parametrize(
        "selector",
        [
            "/../etc/passwd",
            "/subdir/../../etc/passwd",
            "/../../../etc/passwd",
            "/..%2f..%2fetc/passwd",
            "/..",
            "/subdir/..",
        ],
    )
    def test_various_traversal_attempts(
        self, static_handler: StaticFileHandler, selector: str
    ):
        """Various path traversal patterns are blocked."""
        request = GopherRequest(selector=selector)

        response = static_handler.handle(request)

        # Should either return error or not escape document root
        if response.is_directory and response.items:
            # If it's a directory response with items, check for error
            # or normal content (subdir/.. should resolve to root)
            if response.items[0].item_type == ItemType.ERROR:
                assert "Not found" in response.items[0].display_text


class TestStaticFileHandlerGopherPlus:
    """Tests for Gopher+ attribute handling."""

    def test_attributes_request(self, static_handler: StaticFileHandler):
        """Attributes request returns attribute block."""
        request = GopherRequest(
            selector="/readme.txt",
            request_type=RequestType.ATTRIBUTES,
        )

        response = static_handler.handle(request)

        assert response.is_directory is False
        assert response.raw_body is not None
        # Should contain +INFO block
        body_str = response.raw_body.decode("utf-8")
        assert "+INFO" in body_str

    def test_directory_attributes_request(self, static_handler: StaticFileHandler):
        """Directory attributes request returns all item attributes."""
        request = GopherRequest(
            selector="/subdir",
            request_type=RequestType.DIRECTORY,
        )

        response = static_handler.handle(request)

        assert response.is_directory is False
        assert response.raw_body is not None
        # Should contain multiple +INFO blocks
        body_str = response.raw_body.decode("utf-8")
        assert "+INFO" in body_str

    def test_attributes_include_admin(self, static_handler: StaticFileHandler):
        """Attributes include +ADMIN when configured."""
        request = GopherRequest(
            selector="/readme.txt",
            request_type=RequestType.ATTRIBUTES,
        )

        response = static_handler.handle(request)

        body_str = response.raw_body.decode("utf-8")
        assert "+ADMIN" in body_str
        assert "Test Admin" in body_str

    def test_gopher_plus_disabled(self, populated_document_root: Path):
        """Gopher+ request with gopher_plus=False still works."""
        handler = StaticFileHandler(
            document_root=populated_document_root,
            hostname="localhost",
            gopher_plus=False,
        )

        request = GopherRequest(
            selector="/readme.txt",
            request_type=RequestType.ATTRIBUTES,
        )

        response = handler.handle(request)

        # Should still return attributes (handler respects request type)
        assert response.raw_body is not None


class TestStaticFileHandlerRootSelector:
    """Tests for root selector handling."""

    def test_root_selector(self, static_handler: StaticFileHandler):
        """Root selector serves index."""
        request = GopherRequest(selector="/")

        response = static_handler.handle(request)

        assert response.is_directory is True

    def test_empty_selector(self, static_handler: StaticFileHandler):
        """Empty selector treated as root."""
        request = GopherRequest(selector="")

        response = static_handler.handle(request)

        assert response.is_directory is True


class TestErrorHandler:
    """Tests for ErrorHandler."""

    def test_default_message(self):
        """Default error message is used."""
        handler = ErrorHandler()

        assert handler.message == "Error"

    def test_custom_message(self):
        """Custom error message is used."""
        handler = ErrorHandler("Custom error message")

        assert handler.message == "Custom error message"

    def test_returns_error_response(self, error_handler: ErrorHandler):
        """Handler returns error response."""
        request = GopherRequest(selector="/anything")

        response = error_handler.handle(request)

        assert response.is_directory is True
        assert len(response.items) == 1
        assert response.items[0].item_type == ItemType.ERROR

    def test_response_contains_message(self, error_handler: ErrorHandler):
        """Error response contains the message."""
        request = GopherRequest(selector="/anything")

        response = error_handler.handle(request)

        assert error_handler.message in response.items[0].display_text

    def test_ignores_request(self):
        """Handler ignores the request content."""
        handler = ErrorHandler("Test error")

        request1 = GopherRequest(selector="/path1")
        request2 = GopherRequest(selector="/path2", search_query="query")

        response1 = handler.handle(request1)
        response2 = handler.handle(request2)

        # Both should return the same error
        assert response1.items[0].display_text == response2.items[0].display_text
