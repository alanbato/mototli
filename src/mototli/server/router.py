"""Selector routing for Gopher server.

This module provides the Router class for matching selectors to request handlers.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

from ..protocol.request import GopherRequest
from ..protocol.response import GopherResponse, create_error_item


class RouteType(Enum):
    """Type of route pattern matching."""

    EXACT = auto()
    """Exact selector match."""

    PREFIX = auto()
    """Selector prefix match."""


@dataclass
class Route:
    """Represents a selector route.

    Attributes:
        pattern: The selector pattern to match against.
        handler: The callable handler that processes matching requests.
        route_type: The type of matching to perform.
    """

    pattern: str
    handler: Callable[[GopherRequest], GopherResponse]
    route_type: RouteType


class Router:
    """Routes incoming requests to appropriate handlers.

    The Router supports two types of route matching:
    - Exact: Selector must match exactly
    - Prefix: Selector must start with the pattern

    Routes are matched in the order they were registered.

    Examples:
        >>> router = Router()
        >>> router.add_route("/", index_handler)
        >>> router.add_route("/files/", file_handler, route_type=RouteType.PREFIX)
    """

    def __init__(self) -> None:
        """Initialize an empty router."""
        self.routes: list[Route] = []
        self.default_handler: Callable[[GopherRequest], GopherResponse] | None = None

    def add_route(
        self,
        pattern: str,
        handler: Callable[[GopherRequest], GopherResponse],
        route_type: RouteType = RouteType.EXACT,
    ) -> None:
        """Register a new route.

        Args:
            pattern: The selector pattern to match.
            handler: Callable that takes a GopherRequest and returns a GopherResponse.
            route_type: Type of matching to perform (default: EXACT).

        Examples:
            >>> router.add_route("/", index_handler)
            >>> router.add_route("/cgi-bin/", cgi_handler, RouteType.PREFIX)
        """
        route = Route(
            pattern=pattern,
            handler=handler,
            route_type=route_type,
        )
        self.routes.append(route)

    def set_default_handler(
        self, handler: Callable[[GopherRequest], GopherResponse]
    ) -> None:
        """Set the default handler for unmatched routes.

        Args:
            handler: Callable that handles requests not matching any route.
                Typically returns an error response.
        """
        self.default_handler = handler

    def route(self, request: GopherRequest) -> GopherResponse:
        """Route a request to the appropriate handler.

        Routes are matched in the order they were registered.
        If no route matches, the default handler is called (if set),
        otherwise an error response is returned.

        Args:
            request: The incoming request to route.

        Returns:
            The response from the matched handler.
        """
        selector = request.selector

        # Try to match against registered routes
        for route in self.routes:
            if self._matches(selector, route):
                return route.handler(request)

        # No match found, use default handler or return error
        if self.default_handler:
            return self.default_handler(request)

        # No default handler, return generic error
        return GopherResponse(
            items=[create_error_item("Not found")],
            is_directory=True,
        )

    def _matches(self, selector: str, route: Route) -> bool:
        """Check if a selector matches a route.

        Args:
            selector: The request selector to check.
            route: The route to match against.

        Returns:
            True if the selector matches the route, False otherwise.
        """
        if route.route_type == RouteType.EXACT:
            return selector == route.pattern

        elif route.route_type == RouteType.PREFIX:
            return selector.startswith(route.pattern)

        return False
