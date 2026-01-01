"""Tests for Router."""

import pytest

from mototli.protocol.item_types import ItemType
from mototli.protocol.request import GopherRequest
from mototli.protocol.response import GopherItem, GopherResponse
from mototli.server.router import Route, Router, RouteType


class TestRouteType:
    """Tests for RouteType enum."""

    def test_exact_type(self):
        """EXACT route type exists."""
        assert RouteType.EXACT is not None

    def test_prefix_type(self):
        """PREFIX route type exists."""
        assert RouteType.PREFIX is not None

    def test_values_are_distinct(self):
        """Route types have distinct values."""
        assert RouteType.EXACT != RouteType.PREFIX


class TestRoute:
    """Tests for Route dataclass."""

    def test_create_route(self):
        """Create a route with handler."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        route = Route(pattern="/", handler=handler, route_type=RouteType.EXACT)

        assert route.pattern == "/"
        assert route.handler == handler
        assert route.route_type == RouteType.EXACT


class TestRouterCreation:
    """Tests for Router initialization."""

    def test_empty_router(self):
        """New router has no routes."""
        router = Router()

        assert router.routes == []

    def test_no_default_handler(self):
        """New router has no default handler."""
        router = Router()

        assert router.default_handler is None


class TestAddRoute:
    """Tests for Router.add_route()."""

    def test_add_exact_route(self):
        """Add route with exact matching."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        router = Router()
        router.add_route("/", handler)

        assert len(router.routes) == 1
        assert router.routes[0].pattern == "/"
        assert router.routes[0].route_type == RouteType.EXACT

    def test_add_prefix_route(self):
        """Add route with prefix matching."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        router = Router()
        router.add_route("/files/", handler, route_type=RouteType.PREFIX)

        assert len(router.routes) == 1
        assert router.routes[0].route_type == RouteType.PREFIX

    def test_multiple_routes(self):
        """Add multiple routes to router."""

        def handler1(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        def handler2(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        router = Router()
        router.add_route("/", handler1)
        router.add_route("/about", handler2)

        assert len(router.routes) == 2

    def test_route_order_preserved(self):
        """Routes are matched in registration order."""

        def handler1(request: GopherRequest) -> GopherResponse:
            return GopherResponse(items=[GopherItem(ItemType.INFO, "first", "", "host")])

        def handler2(request: GopherRequest) -> GopherResponse:
            return GopherResponse(items=[GopherItem(ItemType.INFO, "second", "", "host")])

        router = Router()
        router.add_route("/test", handler1)
        router.add_route("/test", handler2)

        # First handler should be called
        response = router.route(GopherRequest(selector="/test"))
        assert response.items[0].display_text == "first"


class TestSetDefaultHandler:
    """Tests for Router.set_default_handler()."""

    def test_set_default_handler(self):
        """Set default handler for unmatched routes."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        router = Router()
        router.set_default_handler(handler)

        assert router.default_handler == handler

    def test_default_handler_called(self):
        """Default handler is called when no route matches."""

        def default_handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "default", "", "host")]
            )

        router = Router()
        router.set_default_handler(default_handler)

        response = router.route(GopherRequest(selector="/unknown"))

        assert response.items[0].display_text == "default"


class TestRouterRoute:
    """Tests for Router.route()."""

    def test_exact_match(self):
        """Exact route matches exactly."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "matched", "", "host")]
            )

        router = Router()
        router.add_route("/about", handler)

        response = router.route(GopherRequest(selector="/about"))

        assert response.items[0].display_text == "matched"

    def test_exact_no_match_similar(self):
        """Exact route does not match similar selectors."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "matched", "", "host")]
            )

        router = Router()
        router.add_route("/about", handler)

        # These should NOT match
        response = router.route(GopherRequest(selector="/about/more"))
        assert response.items[0].item_type == ItemType.ERROR

        response = router.route(GopherRequest(selector="/abou"))
        assert response.items[0].item_type == ItemType.ERROR

    def test_prefix_match(self):
        """Prefix route matches selector with prefix."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "matched", "", "host")]
            )

        router = Router()
        router.add_route("/files/", handler, route_type=RouteType.PREFIX)

        response = router.route(GopherRequest(selector="/files/doc.txt"))

        assert response.items[0].display_text == "matched"

    def test_prefix_match_exact(self):
        """Prefix route matches exact pattern too."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "matched", "", "host")]
            )

        router = Router()
        router.add_route("/files/", handler, route_type=RouteType.PREFIX)

        response = router.route(GopherRequest(selector="/files/"))

        assert response.items[0].display_text == "matched"

    def test_prefix_no_partial_match(self):
        """Prefix route doesn't match partial prefix."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "matched", "", "host")]
            )

        router = Router()
        router.add_route("/files/", handler, route_type=RouteType.PREFIX)

        # /file (without s/) should NOT match
        response = router.route(GopherRequest(selector="/file"))

        assert response.items[0].item_type == ItemType.ERROR

    def test_first_match_wins(self):
        """First matching route handler is used."""

        def handler1(request: GopherRequest) -> GopherResponse:
            return GopherResponse(items=[GopherItem(ItemType.INFO, "first", "", "host")])

        def handler2(request: GopherRequest) -> GopherResponse:
            return GopherResponse(items=[GopherItem(ItemType.INFO, "second", "", "host")])

        router = Router()
        # Add prefix route first, then exact route
        router.add_route("/files/", handler1, route_type=RouteType.PREFIX)
        router.add_route("/files/doc.txt", handler2)

        # Prefix should match first
        response = router.route(GopherRequest(selector="/files/doc.txt"))

        assert response.items[0].display_text == "first"

    def test_no_match_uses_default(self):
        """Unmatched selector uses default handler."""

        def specific_handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "specific", "", "host")]
            )

        def default_handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(
                items=[GopherItem(ItemType.INFO, "default", "", "host")]
            )

        router = Router()
        router.add_route("/specific", specific_handler)
        router.set_default_handler(default_handler)

        response = router.route(GopherRequest(selector="/other"))

        assert response.items[0].display_text == "default"

    def test_no_match_no_default_returns_error(self):
        """Unmatched selector without default returns error response."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse()

        router = Router()
        router.add_route("/specific", handler)

        response = router.route(GopherRequest(selector="/other"))

        assert response.is_directory is True
        assert len(response.items) == 1
        assert response.items[0].item_type == ItemType.ERROR
        assert "Not found" in response.items[0].display_text


class TestRouterWithHandlers:
    """Integration tests with actual handlers."""

    def test_route_to_static_handler(self, static_handler):
        """Route correctly calls static handler."""
        router = Router()
        router.add_route("/", static_handler.handle, RouteType.PREFIX)

        response = router.route(GopherRequest(selector="/readme.txt"))

        assert response.is_directory is False
        assert response.raw_body is not None
        assert b"test file" in response.raw_body

    def test_route_to_cgi_handler(self, cgi_handler):
        """Route correctly calls CGI handler."""
        router = Router()
        router.add_route("/cgi-bin/", cgi_handler.handle, RouteType.PREFIX)

        response = router.route(GopherRequest(selector="/cgi-bin/hello.cgi"))

        assert b"Hello from CGI" in response.raw_body

    def test_mixed_handlers(self, static_handler, cgi_handler):
        """Router with multiple handler types works correctly."""
        router = Router()
        router.add_route("/cgi-bin/", cgi_handler.handle, RouteType.PREFIX)
        router.add_route("/", static_handler.handle, RouteType.PREFIX)

        # CGI route
        response = router.route(GopherRequest(selector="/cgi-bin/hello.cgi"))
        assert b"Hello from CGI" in response.raw_body

        # Note: static_handler uses populated_document_root, not cgi_document_root
        # So we need to test with a file that exists in populated_document_root


class TestRouterEdgeCases:
    """Edge case tests for Router."""

    def test_empty_selector(self):
        """Route handles empty selector."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(items=[GopherItem(ItemType.INFO, "root", "", "host")])

        router = Router()
        router.add_route("", handler)

        response = router.route(GopherRequest(selector=""))

        assert response.items[0].display_text == "root"

    def test_root_selector(self):
        """Route handles root selector."""

        def handler(request: GopherRequest) -> GopherResponse:
            return GopherResponse(items=[GopherItem(ItemType.INFO, "root", "", "host")])

        router = Router()
        router.add_route("/", handler)

        response = router.route(GopherRequest(selector="/"))

        assert response.items[0].display_text == "root"

    def test_request_passed_to_handler(self):
        """Request object is passed correctly to handler."""
        received_request = None

        def handler(request: GopherRequest) -> GopherResponse:
            nonlocal received_request
            received_request = request
            return GopherResponse()

        router = Router()
        router.add_route("/", handler, RouteType.PREFIX)

        original_request = GopherRequest(
            selector="/test",
            search_query="query",
        )
        router.route(original_request)

        assert received_request is not None
        assert received_request.selector == "/test"
        assert received_request.search_query == "query"
