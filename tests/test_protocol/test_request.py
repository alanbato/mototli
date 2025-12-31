"""Tests for Gopher request parsing and serialization."""

import pytest

from mototli.protocol.request import GopherRequest, RequestType


class TestRequestType:
    """Tests for RequestType enum."""

    def test_standard_value(self):
        """Standard request has empty modifier."""
        assert RequestType.STANDARD.value == ""

    def test_plus_value(self):
        """Gopher+ request has '+' modifier."""
        assert RequestType.PLUS.value == "+"

    def test_attributes_value(self):
        """Attributes request has '!' modifier."""
        assert RequestType.ATTRIBUTES.value == "!"

    def test_directory_value(self):
        """Directory request has '$' modifier."""
        assert RequestType.DIRECTORY.value == "$"


class TestGopherRequestCreation:
    """Tests for GopherRequest creation."""

    def test_simple_selector(self):
        """Create request with simple selector."""
        request = GopherRequest(selector="/about")
        assert request.selector == "/about"
        assert request.search_query is None
        assert request.request_type == RequestType.STANDARD

    def test_with_search_query(self):
        """Create request with search query."""
        request = GopherRequest(selector="/search", search_query="python")
        assert request.selector == "/search"
        assert request.search_query == "python"

    def test_with_gopher_plus(self):
        """Create Gopher+ request."""
        request = GopherRequest(
            selector="/about",
            request_type=RequestType.PLUS,
        )
        assert request.request_type == RequestType.PLUS
        assert request.is_gopher_plus is True

    def test_with_view_type(self):
        """Create request with specific view type."""
        request = GopherRequest(
            selector="/doc",
            request_type=RequestType.PLUS,
            view_type="text/plain",
        )
        assert request.view_type == "text/plain"

    def test_standard_not_gopher_plus(self):
        """Standard request is not Gopher+."""
        request = GopherRequest(selector="/")
        assert request.is_gopher_plus is False


class TestFromLine:
    """Tests for GopherRequest.from_line() parsing."""

    def test_empty_selector(self):
        """Parse empty selector (root)."""
        request = GopherRequest.from_line(b"")
        assert request.selector == ""

    def test_simple_selector(self):
        """Parse simple selector."""
        request = GopherRequest.from_line(b"/about")
        assert request.selector == "/about"
        assert request.search_query is None

    def test_selector_with_crlf(self):
        """Parse selector with trailing CRLF."""
        request = GopherRequest.from_line(b"/about\r\n")
        assert request.selector == "/about"

    def test_selector_with_search(self):
        """Parse selector with search query."""
        request = GopherRequest.from_line(b"/search\tpython")
        assert request.selector == "/search"
        assert request.search_query == "python"

    def test_selector_with_search_and_crlf(self):
        """Parse selector with search query and CRLF."""
        request = GopherRequest.from_line(b"/search\tpython\r\n")
        assert request.selector == "/search"
        assert request.search_query == "python"

    def test_gopher_plus_request(self):
        """Parse Gopher+ request with + modifier."""
        request = GopherRequest.from_line(b"/about\t+")
        assert request.selector == "/about"
        assert request.request_type == RequestType.PLUS

    def test_gopher_plus_attributes_only(self):
        """Parse Gopher+ attributes-only request."""
        request = GopherRequest.from_line(b"/about\t!")
        assert request.selector == "/about"
        assert request.request_type == RequestType.ATTRIBUTES

    def test_gopher_plus_directory_entry(self):
        """Parse Gopher+ directory entry request."""
        request = GopherRequest.from_line(b"/about\t$")
        assert request.selector == "/about"
        assert request.request_type == RequestType.DIRECTORY

    def test_gopher_plus_with_view_type(self):
        """Parse Gopher+ request with specific view."""
        request = GopherRequest.from_line(b"/doc\t+text/plain")
        assert request.selector == "/doc"
        assert request.request_type == RequestType.PLUS
        assert request.view_type == "text/plain"

    def test_search_with_gopher_plus(self):
        """Parse search with Gopher+ modifier."""
        request = GopherRequest.from_line(b"/search\tquery\t+")
        assert request.selector == "/search"
        assert request.search_query == "query"
        assert request.request_type == RequestType.PLUS

    def test_unicode_selector(self):
        """Parse UTF-8 encoded selector."""
        request = GopherRequest.from_line("/über".encode())
        assert request.selector == "/über"

    def test_latin1_fallback(self):
        """Fall back to latin-1 for non-UTF-8."""
        # Create bytes that are valid latin-1 but not UTF-8
        request = GopherRequest.from_line(b"/caf\xe9")
        assert request.selector == "/café"

    def test_max_selector_size_exceeded(self):
        """Raise error for selector exceeding max size."""
        long_selector = b"/" + b"a" * 300
        with pytest.raises(ValueError, match="exceeds maximum size"):
            GopherRequest.from_line(long_selector)

    def test_max_selector_size_allowed(self):
        """Accept selector at max size."""
        selector = b"/" + b"a" * 253  # 254 chars total, under 255
        request = GopherRequest.from_line(selector)
        assert len(request.selector) == 254


class TestToBytes:
    """Tests for GopherRequest.to_bytes() serialization."""

    def test_simple_selector(self):
        """Serialize simple selector."""
        request = GopherRequest(selector="/about")
        assert request.to_bytes() == b"/about\r\n"

    def test_empty_selector(self):
        """Serialize empty selector (root)."""
        request = GopherRequest(selector="")
        assert request.to_bytes() == b"\r\n"

    def test_with_search_query(self):
        """Serialize with search query."""
        request = GopherRequest(selector="/search", search_query="python")
        assert request.to_bytes() == b"/search\tpython\r\n"

    def test_gopher_plus_request(self):
        """Serialize Gopher+ request."""
        request = GopherRequest(selector="/about", request_type=RequestType.PLUS)
        assert request.to_bytes() == b"/about\t+\r\n"

    def test_gopher_plus_attributes(self):
        """Serialize Gopher+ attributes request."""
        request = GopherRequest(
            selector="/about",
            request_type=RequestType.ATTRIBUTES,
        )
        assert request.to_bytes() == b"/about\t!\r\n"

    def test_gopher_plus_with_view(self):
        """Serialize Gopher+ request with view type."""
        request = GopherRequest(
            selector="/doc",
            request_type=RequestType.PLUS,
            view_type="text/plain",
        )
        assert request.to_bytes() == b"/doc\t+text/plain\r\n"

    def test_search_with_gopher_plus(self):
        """Serialize search with Gopher+ modifier."""
        request = GopherRequest(
            selector="/search",
            search_query="query",
            request_type=RequestType.PLUS,
        )
        assert request.to_bytes() == b"/search\tquery\t+\r\n"

    def test_unicode_selector(self):
        """Serialize UTF-8 selector."""
        request = GopherRequest(selector="/über")
        assert request.to_bytes() == "/über\r\n".encode()


class TestRoundTrip:
    """Tests for parse/serialize round-trip."""

    @pytest.mark.parametrize(
        "line",
        [
            b"/",
            b"/about",
            b"/path/to/file",
            b"/search\tquery",
            b"/about\t+",
            b"/about\t!",
            b"/about\t$",
        ],
    )
    def test_round_trip(self, line):
        """Parsing and serializing should produce equivalent result."""
        request = GopherRequest.from_line(line)
        result = request.to_bytes()
        # Re-parse the result
        reparsed = GopherRequest.from_line(result)
        assert reparsed.selector == request.selector
        assert reparsed.search_query == request.search_query
        assert reparsed.request_type == request.request_type


class TestStringRepresentation:
    """Tests for string representation."""

    def test_str_simple(self):
        """String representation of simple request."""
        request = GopherRequest(selector="/about")
        result = str(request)
        assert "Selector: /about" in result

    def test_str_with_search(self):
        """String representation with search query."""
        request = GopherRequest(selector="/search", search_query="python")
        result = str(request)
        assert "Selector: /search" in result
        assert "Search: python" in result

    def test_str_gopher_plus(self):
        """String representation of Gopher+ request."""
        request = GopherRequest(selector="/about", request_type=RequestType.PLUS)
        result = str(request)
        assert "Type: PLUS" in result

    def test_str_with_view(self):
        """String representation with view type."""
        request = GopherRequest(
            selector="/doc",
            request_type=RequestType.PLUS,
            view_type="text/plain",
        )
        result = str(request)
        assert "View: text/plain" in result
