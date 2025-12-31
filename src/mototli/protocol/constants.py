"""Gopher protocol constants.

This module defines the core constants for the Gopher protocol as specified
in RFC 1436 and Gopher+ extensions (RFC 4266).
"""

# Network constants
DEFAULT_PORT = 70
"""Default TCP port for Gopher protocol."""

# Protocol limits
MAX_SELECTOR_SIZE = 255
"""Maximum size of a Gopher selector in bytes (per RFC 1436)."""

MAX_RESPONSE_BODY_SIZE = 10 * 1024 * 1024  # 10 MB
"""Recommended maximum response body size (not enforced by protocol)."""

DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MiB
"""Default maximum file size to serve."""

MAX_REDIRECTS = 5
"""Maximum number of redirects to follow before stopping."""

REQUEST_TIMEOUT = 30.0
"""Default timeout for requests in seconds."""

# Protocol markers
CRLF = b"\r\n"
"""Carriage Return Line Feed - protocol line terminator."""

TAB = b"\t"
"""Tab character - field separator in Gopher responses."""

GOPHER_TERMINATOR = b".\r\n"
"""Single period on a line - marks end of directory listing."""

# Gopher+ request modifiers
GOPHER_PLUS_REQUEST = b"+"
"""Modifier for Gopher+ request with content."""

GOPHER_PLUS_ATTRIBUTES = b"!"
"""Modifier to request attributes only."""

GOPHER_PLUS_DIRECTORY = b"$"
"""Modifier to request directory entry for item."""

# Gopher+ attribute block markers
ATTR_INFO = "+INFO:"
"""Gopher+ attribute: item information."""

ATTR_ADMIN = "+ADMIN:"
"""Gopher+ attribute: administrative information."""

ATTR_VIEWS = "+VIEWS:"
"""Gopher+ attribute: available views/representations."""

ATTR_ABSTRACT = "+ABSTRACT:"
"""Gopher+ attribute: abstract/description."""

ATTR_ASK = "+ASK:"
"""Gopher+ attribute: form/query definition."""
