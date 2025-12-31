"""Tests for Gopher+ attributes parsing and serialization."""

from datetime import datetime

import pytest

from mototli.protocol.attributes import (
    AskField,
    GopherAttributes,
    ViewInfo,
)


class TestViewInfo:
    """Tests for ViewInfo dataclass."""

    def test_simple_view(self):
        """Create simple view info."""
        view = ViewInfo(mime_type="text/plain")
        assert view.mime_type == "text/plain"
        assert view.language is None
        assert view.size is None
        assert view.size_bytes is None

    def test_view_with_size(self):
        """Create view with size."""
        view = ViewInfo(
            mime_type="application/pdf",
            size="500k",
            size_bytes=512000,
        )
        assert view.mime_type == "application/pdf"
        assert view.size == "500k"
        assert view.size_bytes == 512000

    def test_view_with_language(self):
        """Create view with language."""
        view = ViewInfo(
            mime_type="text/plain",
            language="en_US",
        )
        assert view.language == "en_US"


class TestViewInfoParse:
    """Tests for ViewInfo.parse() method."""

    def test_parse_simple(self):
        """Parse simple MIME type."""
        view = ViewInfo.parse("text/plain:")
        assert view.mime_type == "text/plain"
        assert view.size is None

    def test_parse_with_size(self):
        """Parse MIME type with size."""
        view = ViewInfo.parse("text/plain: <10k>")
        assert view.mime_type == "text/plain"
        assert view.size == "10k"
        assert view.size_bytes == 10 * 1024

    def test_parse_with_language(self):
        """Parse MIME type with language."""
        view = ViewInfo.parse("text/plain en_US: <5k>")
        assert view.mime_type == "text/plain"
        assert view.language == "en_US"
        assert view.size == "5k"

    def test_parse_megabytes(self):
        """Parse size in megabytes."""
        view = ViewInfo.parse("application/pdf: <1.5M>")
        assert view.size == "1.5M"
        assert view.size_bytes == int(1.5 * 1024 * 1024)

    def test_parse_bytes(self):
        """Parse size in bytes."""
        view = ViewInfo.parse("text/plain: <1000>")
        assert view.size == "1000"
        assert view.size_bytes == 1000

    def test_parse_empty(self):
        """Parse empty string."""
        view = ViewInfo.parse("")
        assert view.mime_type == "application/octet-stream"


class TestViewInfoToString:
    """Tests for ViewInfo.to_string() method."""

    def test_simple(self):
        """Serialize simple view."""
        view = ViewInfo(mime_type="text/plain")
        assert view.to_string() == "text/plain:"

    def test_with_size(self):
        """Serialize view with size."""
        view = ViewInfo(mime_type="text/plain", size="10k")
        assert view.to_string() == "text/plain: <10k>"

    def test_with_language(self):
        """Serialize view with language."""
        view = ViewInfo(mime_type="text/plain", language="en_US", size="5k")
        assert view.to_string() == "text/plain en_US: <5k>"


class TestAskField:
    """Tests for AskField dataclass."""

    def test_simple_ask(self):
        """Create simple Ask field."""
        field = AskField(field_type="Ask", prompt="Enter your name:")
        assert field.field_type == "Ask"
        assert field.prompt == "Enter your name:"
        assert field.default is None
        assert field.options == []

    def test_ask_with_default(self):
        """Create Ask field with default value."""
        field = AskField(
            field_type="Ask",
            prompt="Enter value:",
            default="42",
        )
        assert field.default == "42"

    def test_select_with_options(self):
        """Create Select field with options."""
        field = AskField(
            field_type="Select",
            prompt="Choose one:",
            options=["Option A", "Option B", "Option C"],
        )
        assert len(field.options) == 3


class TestGopherAttributesCreation:
    """Tests for GopherAttributes creation."""

    def test_empty_attributes(self):
        """Create empty attributes."""
        attrs = GopherAttributes()
        assert attrs.info is None
        assert attrs.admin is None
        assert attrs.admin_email is None
        assert attrs.mod_date is None
        assert attrs.views == []
        assert attrs.abstract is None

    def test_with_admin(self):
        """Create attributes with admin info."""
        attrs = GopherAttributes(
            admin="John Doe",
            admin_email="john@example.com",
        )
        assert attrs.admin == "John Doe"
        assert attrs.admin_email == "john@example.com"

    def test_with_abstract(self):
        """Create attributes with abstract."""
        attrs = GopherAttributes(abstract="A description of this resource.")
        assert attrs.abstract == "A description of this resource."


class TestGopherAttributesParse:
    """Tests for GopherAttributes.parse() method."""

    def test_parse_info(self):
        """Parse INFO block."""
        block = "+INFO: 0About\t/about\texample.com\t70"
        attrs = GopherAttributes.parse(block)
        assert attrs.info is not None
        assert attrs.info.display_text == "About"
        assert attrs.info.selector == "/about"

    def test_parse_admin_simple(self):
        """Parse simple ADMIN block."""
        block = """+ADMIN:
 Admin: John Doe"""
        attrs = GopherAttributes.parse(block)
        assert attrs.admin == "John Doe"

    def test_parse_admin_with_email(self):
        """Parse ADMIN block with email."""
        block = """+ADMIN:
 Admin: John Doe <john@example.com>"""
        attrs = GopherAttributes.parse(block)
        assert attrs.admin == "John Doe"
        assert attrs.admin_email == "john@example.com"

    def test_parse_mod_date(self):
        """Parse ADMIN block with modification date."""
        block = """+ADMIN:
 Admin: John Doe
 Mod-Date: 2024-01-15T12:00:00"""
        attrs = GopherAttributes.parse(block)
        assert attrs.mod_date is not None
        assert attrs.mod_date.year == 2024
        assert attrs.mod_date.month == 1
        assert attrs.mod_date.day == 15

    def test_parse_views(self):
        """Parse VIEWS block."""
        block = """+VIEWS:
 text/plain: <10k>
 application/pdf: <500k>"""
        attrs = GopherAttributes.parse(block)
        assert len(attrs.views) == 2
        assert attrs.views[0].mime_type == "text/plain"
        assert attrs.views[0].size == "10k"
        assert attrs.views[1].mime_type == "application/pdf"

    def test_parse_abstract(self):
        """Parse ABSTRACT block."""
        block = """+ABSTRACT:
 This is a description of the resource.
 It can span multiple lines."""
        attrs = GopherAttributes.parse(block)
        assert attrs.abstract is not None
        assert "description" in attrs.abstract
        assert "multiple lines" in attrs.abstract

    def test_parse_full_block(self):
        """Parse complete attribute block."""
        block = """+INFO: 0Document\t/doc\texample.com\t70
+ADMIN:
 Admin: Jane Smith <jane@example.com>
 Mod-Date: 2024-06-01T10:30:00
+VIEWS:
 text/plain: <5k>
 text/html: <8k>
+ABSTRACT:
 A sample document for testing."""
        attrs = GopherAttributes.parse(block)
        assert attrs.info is not None
        assert attrs.info.display_text == "Document"
        assert attrs.admin == "Jane Smith"
        assert attrs.admin_email == "jane@example.com"
        assert len(attrs.views) == 2
        assert attrs.abstract == "A sample document for testing."

    def test_parse_preserves_raw(self):
        """Parsing preserves raw attribute block."""
        block = "+INFO: 0Test\t/test\texample.com\t70"
        attrs = GopherAttributes.parse(block)
        assert attrs.raw == block

    def test_parse_empty(self):
        """Parse empty block."""
        attrs = GopherAttributes.parse("")
        assert attrs.info is None
        assert attrs.admin is None


class TestGopherAttributesToString:
    """Tests for GopherAttributes.to_string() method."""

    def test_empty_attributes(self):
        """Serialize empty attributes."""
        attrs = GopherAttributes()
        result = attrs.to_string()
        assert result == ""

    def test_with_admin(self):
        """Serialize with admin info."""
        attrs = GopherAttributes(
            admin="John Doe",
            admin_email="john@example.com",
        )
        result = attrs.to_string()
        assert "+ADMIN:" in result
        assert "Admin: John Doe <john@example.com>" in result

    def test_with_views(self):
        """Serialize with views."""
        attrs = GopherAttributes(
            views=[
                ViewInfo(mime_type="text/plain", size="10k"),
                ViewInfo(mime_type="application/pdf", size="500k"),
            ]
        )
        result = attrs.to_string()
        assert "+VIEWS:" in result
        assert "text/plain:" in result
        assert "application/pdf:" in result

    def test_with_abstract(self):
        """Serialize with abstract."""
        attrs = GopherAttributes(abstract="A description.")
        result = attrs.to_string()
        assert "+ABSTRACT:" in result
        assert "A description." in result

    def test_multiline_abstract(self):
        """Serialize multiline abstract."""
        attrs = GopherAttributes(abstract="Line 1.\nLine 2.")
        result = attrs.to_string()
        lines = result.split("\n")
        # Abstract should have two content lines
        abstract_lines = [line for line in lines if line.startswith(" ")]
        assert len(abstract_lines) == 2


class TestRoundTrip:
    """Tests for parse/serialize round-trip."""

    def test_round_trip_admin(self):
        """Admin info should survive round-trip."""
        original = GopherAttributes(
            admin="John Doe",
            admin_email="john@example.com",
        )
        serialized = original.to_string()
        parsed = GopherAttributes.parse(serialized)
        assert parsed.admin == original.admin
        assert parsed.admin_email == original.admin_email

    def test_round_trip_views(self):
        """Views should survive round-trip."""
        original = GopherAttributes(
            views=[
                ViewInfo(mime_type="text/plain", size="10k"),
            ]
        )
        serialized = original.to_string()
        parsed = GopherAttributes.parse(serialized)
        assert len(parsed.views) == 1
        assert parsed.views[0].mime_type == "text/plain"

    def test_round_trip_abstract(self):
        """Abstract should survive round-trip."""
        original = GopherAttributes(abstract="A test description.")
        serialized = original.to_string()
        parsed = GopherAttributes.parse(serialized)
        assert parsed.abstract == original.abstract
