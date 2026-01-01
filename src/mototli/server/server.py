"""Gopher server main module.

This module provides the main GopherServer class and functions
for starting and running a Gopher server.
"""

import asyncio
import signal
from pathlib import Path

from ..protocol.request import GopherRequest
from ..protocol.response import GopherResponse
from .cgi import CGIHandler
from .config import ServerConfig
from .handler import ErrorHandler, StaticFileHandler
from .protocol import GopherServerProtocol
from .router import Router, RouteType


class GopherServer:
    """High-level Gopher server.

    This class provides a simple interface for creating and running
    a Gopher server with static file serving, CGI support, and
    Gopher+ extensions.

    Attributes:
        config: Server configuration.
        router: Request router.
        server: The asyncio server object when running.

    Examples:
        >>> config = ServerConfig(
        ...     host="localhost",
        ...     port=70,
        ...     document_root=Path("/var/gopher"),
        ... )
        >>> server = GopherServer(config)
        >>> await server.start()
    """

    def __init__(self, config: ServerConfig) -> None:
        """Initialize the Gopher server.

        Args:
            config: Server configuration.
        """
        self.config = config
        self.router = Router()
        self.server: asyncio.Server | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up default routes and handlers."""
        # Create CGI handler for cgi-bin directories
        cgi_handler = CGIHandler(
            document_root=self.config.document_root,
            hostname=self.config.public_hostname,
            port=self.config.public_port,
            cgi_extensions=self.config.cgi_extensions,
            cgi_directories=self.config.cgi_directories,
            timeout=self.config.cgi_timeout,
            gopher_plus=self.config.gopher_plus,
        )

        # Create static file handler
        static_handler = StaticFileHandler(
            document_root=self.config.document_root,
            hostname=self.config.public_hostname,
            port=self.config.public_port,
            default_indices=self.config.default_indices,
            enable_directory_listing=self.config.enable_directory_listing,
            max_file_size=self.config.max_file_size,
            gopher_plus=self.config.gopher_plus,
            admin_name=self.config.admin_name,
            admin_email=self.config.admin_email,
        )

        # Add CGI routes for each cgi directory
        for cgi_dir in self.config.cgi_directories:
            pattern = "/" + cgi_dir + "/"
            self.router.add_route(
                pattern,
                cgi_handler.handle,
                route_type=RouteType.PREFIX,
            )

        # Add static file handler as default for all paths
        self.router.add_route(
            "/",
            self._create_combined_handler(cgi_handler, static_handler),
            route_type=RouteType.PREFIX,
        )

        # Set error handler for unmatched routes
        error_handler = ErrorHandler("Not found")
        self.router.set_default_handler(error_handler.handle)

    def _create_combined_handler(
        self, cgi_handler: CGIHandler, static_handler: StaticFileHandler
    ):
        """Create a handler that checks for CGI scripts first.

        Args:
            cgi_handler: The CGI handler.
            static_handler: The static file handler.

        Returns:
            A combined handler function.
        """

        def combined_handler(request: GopherRequest) -> GopherResponse:
            # Check if this is a CGI script by extension
            if cgi_handler.can_handle(request.selector):
                return cgi_handler.handle(request)
            # Otherwise use static handler
            return static_handler.handle(request)

        return combined_handler

    async def start(self) -> None:
        """Start the server.

        Creates the asyncio server and starts listening for connections.

        Raises:
            OSError: If unable to bind to the specified host/port.
        """
        # Validate configuration
        self.config.validate()

        # Get event loop
        loop = asyncio.get_running_loop()

        # Create server
        self.server = await loop.create_server(
            lambda: GopherServerProtocol(
                request_handler=self.router.route,
                request_timeout=self.config.request_timeout,
            ),
            self.config.host,
            self.config.port,
        )

        print(f"Gopher server started on {self.config.host}:{self.config.port}")
        print(f"Document root: {self.config.document_root}")
        if self.config.gopher_plus:
            print("Gopher+ enabled")

    async def serve_forever(self) -> None:
        """Run the server forever.

        This method blocks until the server is stopped.
        """
        if not self.server:
            await self.start()

        if self.server:
            async with self.server:
                await self.server.serve_forever()

    async def stop(self) -> None:
        """Stop the server gracefully."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
            print("Gopher server stopped")


async def run_server(config: ServerConfig) -> None:
    """Run a Gopher server with the given configuration.

    This is a convenience function that creates a server and runs it
    until interrupted (Ctrl+C).

    Args:
        config: Server configuration.

    Examples:
        >>> config = ServerConfig(
        ...     host="localhost",
        ...     port=70,
        ...     document_root=Path("/var/gopher"),
        ... )
        >>> asyncio.run(run_server(config))
    """
    server = GopherServer(config)

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    def signal_handler() -> None:
        print("\nShutting down...")
        asyncio.create_task(server.stop())

    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass

    try:
        await server.serve_forever()
    except asyncio.CancelledError:
        await server.stop()


async def start_server(
    host: str = "localhost",
    port: int = 70,
    document_root: Path | str = ".",
    hostname: str | None = None,
    enable_directory_listing: bool = True,
    gopher_plus: bool = True,
    admin_name: str | None = None,
    admin_email: str | None = None,
) -> None:
    """Start a Gopher server with the given options.

    This is a convenience function that creates a configuration and runs
    the server.

    Args:
        host: Host address to bind to.
        port: Port to listen on.
        document_root: Path to the document root directory.
        hostname: Public hostname for menu items. If None, uses host.
        enable_directory_listing: Whether to generate directory listings.
        gopher_plus: Whether Gopher+ is enabled.
        admin_name: Administrator name for Gopher+ ADMIN block.
        admin_email: Administrator email for Gopher+ ADMIN block.

    Examples:
        >>> asyncio.run(start_server(
        ...     host="0.0.0.0",
        ...     port=70,
        ...     document_root="/var/gopher",
        ...     hostname="gopher.example.com",
        ... ))
    """
    config = ServerConfig(
        host=host,
        port=port,
        document_root=Path(document_root),
        hostname=hostname,
        enable_directory_listing=enable_directory_listing,
        gopher_plus=gopher_plus,
        admin_name=admin_name,
        admin_email=admin_email,
    )

    await run_server(config)
