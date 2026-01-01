"""Gopher server implementation.

This package provides a complete Gopher+ server with static file serving,
CGI support, and pluggable request handlers.

Main components:
- GopherServer: High-level server class
- GopherServerProtocol: asyncio Protocol for connections
- ServerConfig: Server configuration
- Router: Selector-based request routing
- StaticFileHandler: Static file and directory serving
- CGIHandler: CGI script execution

Example:
    >>> from mototli.server import GopherServer, ServerConfig
    >>> from pathlib import Path
    >>>
    >>> config = ServerConfig(
    ...     host="localhost",
    ...     port=70,
    ...     document_root=Path("/var/gopher"),
    ... )
    >>> server = GopherServer(config)
    >>> # await server.serve_forever()
"""

from .cgi import CGIHandler
from .config import ServerConfig
from .handler import ErrorHandler, RequestHandler, StaticFileHandler
from .protocol import GopherPlusServerProtocol, GopherServerProtocol
from .router import Router, RouteType
from .server import GopherServer, run_server, start_server

__all__ = [
    # Server
    "GopherServer",
    "run_server",
    "start_server",
    # Protocol
    "GopherServerProtocol",
    "GopherPlusServerProtocol",
    # Configuration
    "ServerConfig",
    # Routing
    "Router",
    "RouteType",
    # Handlers
    "RequestHandler",
    "StaticFileHandler",
    "CGIHandler",
    "ErrorHandler",
]
