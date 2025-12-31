"""Tests for protocol constants."""

import pytest

from mototli.protocol.constants import (
    ATTR_ABSTRACT,
    ATTR_ADMIN,
    ATTR_INFO,
    ATTR_VIEWS,
    CRLF,
    DEFAULT_MAX_FILE_SIZE,
    DEFAULT_PORT,
    GOPHER_PLUS_ATTRIBUTES,
    GOPHER_PLUS_DIRECTORY,
    GOPHER_PLUS_REQUEST,
    GOPHER_TERMINATOR,
    MAX_REDIRECTS,
    MAX_RESPONSE_BODY_SIZE,
    MAX_SELECTOR_SIZE,
    REQUEST_TIMEOUT,
    TAB,
)


class TestNetworkConstants:
    """Tests for network-related constants."""

    def test_default_port(self):
        """Default Gopher port should be 70."""
        assert DEFAULT_PORT == 70

    def test_request_timeout(self):
        """Request timeout should be 30 seconds."""
        assert REQUEST_TIMEOUT == 30.0


class TestProtocolLimits:
    """Tests for protocol limit constants."""

    def test_max_selector_size(self):
        """Max selector size should be 255 per RFC 1436."""
        assert MAX_SELECTOR_SIZE == 255

    def test_max_response_body_size(self):
        """Max response body should be 10 MB."""
        assert MAX_RESPONSE_BODY_SIZE == 10 * 1024 * 1024

    def test_default_max_file_size(self):
        """Default max file size should be 100 MiB."""
        assert DEFAULT_MAX_FILE_SIZE == 100 * 1024 * 1024

    def test_max_redirects(self):
        """Max redirects should be 5."""
        assert MAX_REDIRECTS == 5


class TestProtocolMarkers:
    """Tests for protocol marker constants."""

    def test_crlf(self):
        """CRLF should be carriage return + line feed."""
        assert CRLF == b"\r\n"

    def test_tab(self):
        """TAB should be tab character."""
        assert TAB == b"\t"

    def test_gopher_terminator(self):
        """Gopher terminator should be period + CRLF."""
        assert GOPHER_TERMINATOR == b".\r\n"


class TestGopherPlusModifiers:
    """Tests for Gopher+ request modifier constants."""

    def test_gopher_plus_request(self):
        """Gopher+ request modifier should be '+'."""
        assert GOPHER_PLUS_REQUEST == b"+"

    def test_gopher_plus_attributes(self):
        """Gopher+ attributes modifier should be '!'."""
        assert GOPHER_PLUS_ATTRIBUTES == b"!"

    def test_gopher_plus_directory(self):
        """Gopher+ directory modifier should be '$'."""
        assert GOPHER_PLUS_DIRECTORY == b"$"


class TestAttributeMarkers:
    """Tests for Gopher+ attribute block markers."""

    def test_attr_info(self):
        """INFO attribute marker."""
        assert ATTR_INFO == "+INFO:"

    def test_attr_admin(self):
        """ADMIN attribute marker."""
        assert ATTR_ADMIN == "+ADMIN:"

    def test_attr_views(self):
        """VIEWS attribute marker."""
        assert ATTR_VIEWS == "+VIEWS:"

    def test_attr_abstract(self):
        """ABSTRACT attribute marker."""
        assert ATTR_ABSTRACT == "+ABSTRACT:"
