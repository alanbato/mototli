"""Tests for Gopher response parsing and serialization."""

import pytest

from mototli.protocol.item_types import ItemType
from mototli.protocol.response import (
    GopherItem,
    GopherResponse,
    create_error_item,
    create_info_item,
)


class TestGopherItemCreation:
    """Tests for GopherItem creation."""

    def test_simple_item(self):
        """Create simple item."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="About",
            selector="/about",
            hostname="example.com",
        )
        assert item.item_type == ItemType.TEXT
        assert item.display_text == "About"
        assert item.selector == "/about"
        assert item.hostname == "example.com"
        assert item.port == 70  # Default port

    def test_item_with_custom_port(self):
        """Create item with custom port."""
        item = GopherItem(
            item_type=ItemType.DIRECTORY,
            display_text="Other Server",
            selector="/",
            hostname="other.example.com",
            port=7070,
        )
        assert item.port == 7070

    def test_gopher_plus_item(self):
        """Create Gopher+ enabled item."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="Document",
            selector="/doc",
            hostname="example.com",
            gopher_plus=True,
        )
        assert item.gopher_plus is True

    def test_item_is_frozen(self):
        """GopherItem should be immutable."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="Test",
            selector="/test",
            hostname="example.com",
        )
        with pytest.raises(AttributeError):
            item.display_text = "Changed"


class TestGopherItemFromLine:
    """Tests for GopherItem.from_line() parsing."""

    def test_parse_text_item(self):
        """Parse text item."""
        line = b"0About this server\t/about\texample.com\t70\r\n"
        item = GopherItem.from_line(line)
        assert item.item_type == ItemType.TEXT
        assert item.display_text == "About this server"
        assert item.selector == "/about"
        assert item.hostname == "example.com"
        assert item.port == 70

    def test_parse_directory_item(self):
        """Parse directory item."""
        line = b"1Files\t/files\texample.com\t70\r\n"
        item = GopherItem.from_line(line)
        assert item.item_type == ItemType.DIRECTORY
        assert item.display_text == "Files"

    def test_parse_search_item(self):
        """Parse search item."""
        line = b"7Search\t/search\texample.com\t70\r\n"
        item = GopherItem.from_line(line)
        assert item.item_type == ItemType.SEARCH

    def test_parse_info_item(self):
        """Parse informational item."""
        line = b"iWelcome to our server!\t\terror.host\t0\r\n"
        item = GopherItem.from_line(line)
        assert item.item_type == ItemType.INFO
        assert item.display_text == "Welcome to our server!"

    def test_parse_error_item(self):
        """Parse error item."""
        line = b"3File not found\t\terror.host\t0\r\n"
        item = GopherItem.from_line(line)
        assert item.item_type == ItemType.ERROR
        assert item.display_text == "File not found"

    def test_parse_gopher_plus_item(self):
        """Parse Gopher+ enabled item (trailing +)."""
        line = b"0Document\t/doc\texample.com\t70+\r\n"
        item = GopherItem.from_line(line)
        assert item.gopher_plus is True
        assert item.port == 70

    def test_parse_without_crlf(self):
        """Parse item without trailing CRLF."""
        line = b"0About\t/about\texample.com\t70"
        item = GopherItem.from_line(line)
        assert item.display_text == "About"

    def test_parse_custom_port(self):
        """Parse item with custom port."""
        line = b"1Other\t/\tother.example.com\t7070\r\n"
        item = GopherItem.from_line(line)
        assert item.port == 7070

    def test_parse_unknown_type(self):
        """Unknown type should default to INFO."""
        line = b"XUnknown\t/x\texample.com\t70\r\n"
        item = GopherItem.from_line(line)
        assert item.item_type == ItemType.INFO

    def test_parse_malformed_minimal(self):
        """Malformed line with minimal data."""
        line = b"iJust text"
        item = GopherItem.from_line(line)
        assert item.item_type == ItemType.INFO
        assert item.display_text == "Just text"
        assert item.selector == ""
        assert item.hostname == ""

    def test_parse_empty_raises(self):
        """Empty line should raise ValueError."""
        with pytest.raises(ValueError, match="Empty line"):
            GopherItem.from_line(b"")

    def test_parse_unicode(self):
        """Parse UTF-8 encoded item."""
        line = "0Über uns\t/ueber\texample.com\t70\r\n".encode()
        item = GopherItem.from_line(line)
        assert item.display_text == "Über uns"

    def test_parse_latin1_fallback(self):
        """Fall back to latin-1 for non-UTF-8."""
        line = b"0Caf\xe9\t/cafe\texample.com\t70\r\n"
        item = GopherItem.from_line(line)
        assert item.display_text == "Café"


class TestGopherItemToLine:
    """Tests for GopherItem.to_line() serialization."""

    def test_serialize_text_item(self):
        """Serialize text item."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="About",
            selector="/about",
            hostname="example.com",
        )
        assert item.to_line() == b"0About\t/about\texample.com\t70\r\n"

    def test_serialize_directory_item(self):
        """Serialize directory item."""
        item = GopherItem(
            item_type=ItemType.DIRECTORY,
            display_text="Files",
            selector="/files",
            hostname="example.com",
        )
        assert item.to_line() == b"1Files\t/files\texample.com\t70\r\n"

    def test_serialize_gopher_plus(self):
        """Serialize Gopher+ item."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="Doc",
            selector="/doc",
            hostname="example.com",
            gopher_plus=True,
        )
        assert item.to_line() == b"0Doc\t/doc\texample.com\t70+\r\n"

    def test_serialize_custom_port(self):
        """Serialize item with custom port."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="Other",
            selector="/",
            hostname="other.com",
            port=7070,
        )
        assert item.to_line() == b"0Other\t/\tother.com\t7070\r\n"


class TestGopherItemProperties:
    """Tests for GopherItem properties."""

    def test_is_selectable_text(self):
        """Text item should be selectable."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="Doc",
            selector="/doc",
            hostname="example.com",
        )
        assert item.is_selectable is True

    def test_is_selectable_directory(self):
        """Directory item should be selectable."""
        item = GopherItem(
            item_type=ItemType.DIRECTORY,
            display_text="Dir",
            selector="/dir",
            hostname="example.com",
        )
        assert item.is_selectable is True

    def test_is_not_selectable_info(self):
        """Info item should not be selectable."""
        item = GopherItem(
            item_type=ItemType.INFO,
            display_text="Info",
            selector="",
            hostname="null.host",
        )
        assert item.is_selectable is False

    def test_is_not_selectable_error(self):
        """Error item should not be selectable."""
        item = GopherItem(
            item_type=ItemType.ERROR,
            display_text="Error",
            selector="",
            hostname="error.host",
        )
        assert item.is_selectable is False

    def test_str_representation(self):
        """String representation shows type and text."""
        item = GopherItem(
            item_type=ItemType.TEXT,
            display_text="About",
            selector="/about",
            hostname="example.com",
        )
        assert str(item) == "[0] About"


class TestGopherResponseCreation:
    """Tests for GopherResponse creation."""

    def test_directory_response(self):
        """Create directory response with items."""
        items = [
            GopherItem(ItemType.TEXT, "About", "/about", "example.com"),
            GopherItem(ItemType.DIRECTORY, "Files", "/files", "example.com"),
        ]
        response = GopherResponse(items=items)
        assert len(response.items) == 2
        assert response.is_directory is True
        assert response.raw_body is None

    def test_text_response(self):
        """Create text response with raw body."""
        response = GopherResponse(
            raw_body=b"Hello, World!",
            is_directory=False,
        )
        assert response.raw_body == b"Hello, World!"
        assert response.is_directory is False
        assert len(response.items) == 0


class TestGopherResponseFromBytes:
    """Tests for GopherResponse.from_bytes() parsing."""

    def test_parse_directory(self):
        """Parse directory listing."""
        data = (
            b"0About\t/about\texample.com\t70\r\n"
            b"1Files\t/files\texample.com\t70\r\n"
            b".\r\n"
        )
        response = GopherResponse.from_bytes(data)
        assert response.is_directory is True
        assert len(response.items) == 2
        assert response.items[0].item_type == ItemType.TEXT
        assert response.items[1].item_type == ItemType.DIRECTORY

    def test_parse_with_info_lines(self):
        """Parse directory with info lines."""
        data = (
            b"iWelcome!\t\terror.host\t0\r\n"
            b"i\t\terror.host\t0\r\n"
            b"0About\t/about\texample.com\t70\r\n"
            b".\r\n"
        )
        response = GopherResponse.from_bytes(data)
        assert len(response.items) == 3
        assert response.items[0].item_type == ItemType.INFO

    def test_parse_text_content(self):
        """Parse as text content (not directory)."""
        data = b"Hello, World!\r\nThis is a text file.\r\n"
        response = GopherResponse.from_bytes(data, is_directory=False)
        assert response.is_directory is False
        assert response.raw_body == data
        assert len(response.items) == 0

    def test_parse_skips_terminator(self):
        """Terminator line should not become an item."""
        data = b"0About\t/about\texample.com\t70\r\n.\r\n"
        response = GopherResponse.from_bytes(data)
        assert len(response.items) == 1

    def test_parse_skips_empty_lines(self):
        """Empty lines should be skipped."""
        data = (
            b"0About\t/about\texample.com\t70\r\n"
            b"\r\n"
            b"1Files\t/files\texample.com\t70\r\n"
            b".\r\n"
        )
        response = GopherResponse.from_bytes(data)
        assert len(response.items) == 2


class TestGopherResponseToBytes:
    """Tests for GopherResponse.to_bytes() serialization."""

    def test_serialize_directory(self):
        """Serialize directory listing."""
        items = [
            GopherItem(ItemType.TEXT, "About", "/about", "example.com"),
            GopherItem(ItemType.DIRECTORY, "Files", "/files", "example.com"),
        ]
        response = GopherResponse(items=items)
        result = response.to_bytes()
        assert b"0About\t/about\texample.com\t70\r\n" in result
        assert b"1Files\t/files\texample.com\t70\r\n" in result
        assert result.endswith(b".\r\n")

    def test_serialize_text_content(self):
        """Serialize text content."""
        response = GopherResponse(
            raw_body=b"Hello, World!",
            is_directory=False,
        )
        assert response.to_bytes() == b"Hello, World!"

    def test_serialize_empty_directory(self):
        """Serialize empty directory."""
        response = GopherResponse(items=[])
        assert response.to_bytes() == b".\r\n"


class TestGopherResponseProperties:
    """Tests for GopherResponse properties."""

    def test_text_property(self):
        """Text property decodes raw body."""
        response = GopherResponse(
            raw_body=b"Hello, World!",
            is_directory=False,
        )
        assert response.text == "Hello, World!"

    def test_text_property_unicode(self):
        """Text property handles UTF-8."""
        response = GopherResponse(
            raw_body="Héllo, Wörld!".encode(),
            is_directory=False,
        )
        assert response.text == "Héllo, Wörld!"

    def test_text_property_latin1_fallback(self):
        """Text property falls back to latin-1."""
        response = GopherResponse(
            raw_body=b"Caf\xe9",
            is_directory=False,
        )
        assert response.text == "Café"

    def test_text_property_none_for_directory(self):
        """Text property is None for directory."""
        response = GopherResponse(items=[])
        assert response.text is None

    def test_text_property_none_for_empty_body(self):
        """Text property is None for None body."""
        response = GopherResponse(is_directory=False)
        assert response.text is None

    def test_str_directory(self):
        """String representation of directory."""
        items = [
            GopherItem(ItemType.TEXT, "About", "/about", "example.com"),
        ]
        response = GopherResponse(items=items)
        assert "GopherDirectory(1 items)" in str(response)

    def test_str_text(self):
        """String representation of text response."""
        response = GopherResponse(
            raw_body=b"Hello",
            is_directory=False,
        )
        assert "GopherResponse(5 bytes)" in str(response)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_info_item(self):
        """Create informational item."""
        item = create_info_item("Welcome!")
        assert item.item_type == ItemType.INFO
        assert item.display_text == "Welcome!"
        assert item.selector == ""
        assert item.hostname == "null.host"
        assert item.port == 0

    def test_create_info_item_custom_host(self):
        """Create info item with custom hostname."""
        item = create_info_item("Info", hostname="info.host")
        assert item.hostname == "info.host"

    def test_create_error_item(self):
        """Create error item."""
        item = create_error_item("File not found")
        assert item.item_type == ItemType.ERROR
        assert item.display_text == "File not found"
        assert item.hostname == "error.host"

    def test_create_error_item_custom_host(self):
        """Create error item with custom hostname."""
        item = create_error_item("Error", hostname="err.example.com")
        assert item.hostname == "err.example.com"


class TestRoundTrip:
    """Tests for parse/serialize round-trip."""

    def test_round_trip_directory(self):
        """Directory round-trip should preserve items."""
        original_data = (
            b"0About\t/about\texample.com\t70\r\n"
            b"1Files\t/files\texample.com\t70\r\n"
            b".\r\n"
        )
        response = GopherResponse.from_bytes(original_data)
        serialized = response.to_bytes()
        reparsed = GopherResponse.from_bytes(serialized)

        assert len(reparsed.items) == len(response.items)
        for orig, new in zip(response.items, reparsed.items, strict=True):
            assert orig.item_type == new.item_type
            assert orig.display_text == new.display_text
            assert orig.selector == new.selector
            assert orig.hostname == new.hostname
            assert orig.port == new.port
