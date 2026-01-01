"""Request handlers for Gopher server.

This module provides request handler classes for processing Gopher requests
and generating responses.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..content.attributes import generate_attributes, generate_directory_attributes
from ..content.directory import generate_directory_listing
from ..protocol.constants import DEFAULT_PORT
from ..protocol.item_types import ItemType
from ..protocol.request import GopherRequest, RequestType
from ..protocol.response import (
    GopherItem,
    GopherResponse,
    create_error_item,
    create_info_item,
)
from ..utils.mime import get_item_type


class RequestHandler(ABC):
    """Abstract base class for request handlers.

    All request handlers should inherit from this class and implement
    the handle() method.
    """

    @abstractmethod
    def handle(self, request: GopherRequest) -> GopherResponse:
        """Handle a Gopher request and return a response.

        Args:
            request: The incoming request to handle.

        Returns:
            A GopherResponse object.
        """
        pass


class StaticFileHandler(RequestHandler):
    """Handler for serving static files from a document root.

    This handler serves files from a specified directory with path traversal
    protection, automatic directory listings, and Gopher+ attribute support.

    Attributes:
        document_root: Path to the directory containing files to serve.
        hostname: Server hostname for generating menu items.
        port: Server port for generating menu items.
        default_indices: List of index filenames to try for directory requests.
        enable_directory_listing: Whether to generate directory listings.
        max_file_size: Maximum file size to serve in bytes.
        gopher_plus: Whether Gopher+ is enabled.
        admin_name: Administrator name for Gopher+ ADMIN block.
        admin_email: Administrator email for Gopher+ ADMIN block.

    Examples:
        >>> handler = StaticFileHandler(
        ...     Path("/var/gopher"),
        ...     hostname="gopher.example.com",
        ... )
        >>> request = GopherRequest(selector="/readme.txt")
        >>> response = handler.handle(request)
    """

    def __init__(
        self,
        document_root: Path | str,
        hostname: str,
        port: int = DEFAULT_PORT,
        default_indices: list[str] | None = None,
        enable_directory_listing: bool = True,
        max_file_size: int = 100 * 1024 * 1024,
        gopher_plus: bool = True,
        admin_name: str | None = None,
        admin_email: str | None = None,
    ) -> None:
        """Initialize the static file handler.

        Args:
            document_root: Path to the directory containing files to serve.
            hostname: Server hostname for generating menu items.
            port: Server port for generating menu items.
            default_indices: List of index filenames to try for directory requests.
            enable_directory_listing: Whether to generate directory listings.
            max_file_size: Maximum file size to serve in bytes.
            gopher_plus: Whether Gopher+ is enabled.
            admin_name: Administrator name for Gopher+ ADMIN block.
            admin_email: Administrator email for Gopher+ ADMIN block.
        """
        self.document_root = Path(document_root).resolve()
        self.hostname = hostname
        self.port = port
        self.default_indices = default_indices or [
            "index.gph",
            "gophermap",
            "index.txt",
        ]
        self.enable_directory_listing = enable_directory_listing
        self.max_file_size = max_file_size
        self.gopher_plus = gopher_plus
        self.admin_name = admin_name
        self.admin_email = admin_email

        if not self.document_root.exists():
            raise ValueError(f"Document root does not exist: {self.document_root}")
        if not self.document_root.is_dir():
            raise ValueError(f"Document root is not a directory: {self.document_root}")

    def handle(self, request: GopherRequest) -> GopherResponse:
        """Handle a request for a static file or directory.

        Args:
            request: The incoming request.

        Returns:
            A GopherResponse with the file contents, directory listing,
            or Gopher+ attributes.
        """
        # Get the requested path
        selector = request.selector.lstrip("/")
        if selector == "":
            selector = "."

        # Construct the full file path
        file_path = (self.document_root / selector).resolve()

        # Path traversal protection
        if not self._is_safe_path(file_path):
            return GopherResponse(
                items=[create_error_item("Not found")],
                is_directory=True,
            )

        # Check if path exists
        if not file_path.exists():
            return GopherResponse(
                items=[create_error_item("Not found")],
                is_directory=True,
            )

        # Handle Gopher+ attribute requests
        if request.request_type == RequestType.ATTRIBUTES:
            return self._handle_attributes_request(request, file_path)

        # Handle Gopher+ directory attribute requests
        if request.request_type == RequestType.DIRECTORY:
            return self._handle_directory_attributes_request(request, file_path)

        # Handle directory
        if file_path.is_dir():
            return self._handle_directory(request, file_path)

        # Handle file
        return self._handle_file(request, file_path)

    def _handle_directory(self, request: GopherRequest, path: Path) -> GopherResponse:
        """Handle a directory request.

        Args:
            request: The incoming request.
            path: Path to the directory.

        Returns:
            A directory listing or index file contents.
        """
        # Try to find an index file
        for index_name in self.default_indices:
            index_path = path / index_name
            if index_path.exists() and index_path.is_file():
                return self._handle_file(request, index_path)

        # Generate directory listing if enabled
        if self.enable_directory_listing:
            items = generate_directory_listing(
                path=path,
                selector_base=request.selector or "/",
                hostname=self.hostname,
                port=self.port,
                gopher_plus=self.gopher_plus,
            )
            return GopherResponse(items=items, is_directory=True)

        # Directory listing disabled
        return GopherResponse(
            items=[create_error_item("Not found")],
            is_directory=True,
        )

    def _handle_file(self, request: GopherRequest, path: Path) -> GopherResponse:
        """Handle a file request.

        Args:
            request: The incoming request.
            path: Path to the file.

        Returns:
            The file contents as a GopherResponse.
        """
        # Check file size
        try:
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return GopherResponse(
                    items=[create_error_item("File too large")],
                    is_directory=True,
                )
        except OSError:
            return GopherResponse(
                items=[create_error_item("Cannot read file")],
                is_directory=True,
            )

        # Check if this is a gophermap file
        if path.name in ("gophermap", "index.gph"):
            return self._handle_gophermap(path)

        # Determine if this is a text or binary file
        item_type = get_item_type(path)

        try:
            if item_type.is_text or item_type == ItemType.HTML:
                # Read as text
                content = path.read_text(encoding="utf-8")
                return GopherResponse(
                    raw_body=content.encode("utf-8"),
                    is_directory=False,
                )
            else:
                # Read as binary
                content = path.read_bytes()
                return GopherResponse(
                    raw_body=content,
                    is_directory=False,
                )

        except UnicodeDecodeError:
            # Fall back to binary if UTF-8 decode fails
            content = path.read_bytes()
            return GopherResponse(
                raw_body=content,
                is_directory=False,
            )

        except PermissionError:
            return GopherResponse(
                items=[create_error_item("Permission denied")],
                is_directory=True,
            )

        except OSError as e:
            return GopherResponse(
                items=[create_error_item(f"Cannot read file: {e}")],
                is_directory=True,
            )

    def _handle_gophermap(self, path: Path) -> GopherResponse:
        """Handle a gophermap file.

        Gophermap files are parsed as pre-formatted directory listings.

        Args:
            path: Path to the gophermap file.

        Returns:
            A parsed directory listing.
        """
        items: list[GopherItem] = []

        try:
            content = path.read_text(encoding="utf-8")
            for line in content.splitlines():
                # Skip empty lines
                if not line:
                    items.append(create_info_item("", self.hostname))
                    continue

                # Try to parse as a gophermap line
                item = self._parse_gophermap_line(line)
                if item:
                    items.append(item)
                else:
                    # Treat as info line
                    items.append(create_info_item(line, self.hostname))

        except (OSError, UnicodeDecodeError) as e:
            items.append(create_error_item(f"Cannot read gophermap: {e}"))

        return GopherResponse(items=items, is_directory=True)

    def _parse_gophermap_line(self, line: str) -> GopherItem | None:
        """Parse a single gophermap line.

        Args:
            line: A line from a gophermap file.

        Returns:
            A GopherItem if the line is valid, None otherwise.
        """
        # Lines with tabs are directory entries
        if "\t" not in line:
            return None

        parts = line.split("\t")
        if len(parts) < 2:
            return None

        # First character is the item type
        type_and_text = parts[0]
        if not type_and_text:
            return None

        type_char = type_and_text[0]
        display_text = type_and_text[1:]

        try:
            item_type = ItemType.from_char(type_char)
        except ValueError:
            item_type = ItemType.INFO

        selector = parts[1] if len(parts) > 1 else ""
        hostname = parts[2] if len(parts) > 2 else self.hostname
        try:
            port = int(parts[3]) if len(parts) > 3 else self.port
        except ValueError:
            port = self.port

        return GopherItem(
            item_type=item_type,
            display_text=display_text,
            selector=selector,
            hostname=hostname,
            port=port,
            gopher_plus=self.gopher_plus,
        )

    def _handle_attributes_request(
        self, request: GopherRequest, path: Path
    ) -> GopherResponse:
        """Handle a Gopher+ attributes request.

        Args:
            request: The incoming request.
            path: Path to the file or directory.

        Returns:
            Gopher+ attribute block as response.
        """
        attrs = generate_attributes(
            path=path,
            selector=request.selector,
            hostname=self.hostname,
            port=self.port,
            admin_name=self.admin_name,
            admin_email=self.admin_email,
        )

        # Return attributes as raw text
        return GopherResponse(
            raw_body=attrs.to_string().encode("utf-8"),
            is_directory=False,
            attributes=attrs,
        )

    def _handle_directory_attributes_request(
        self, request: GopherRequest, path: Path
    ) -> GopherResponse:
        """Handle a Gopher+ directory attributes request.

        Args:
            request: The incoming request.
            path: Path to the directory.

        Returns:
            Gopher+ attribute blocks for all items in the directory.
        """
        if not path.is_dir():
            return self._handle_attributes_request(request, path)

        attrs_list = generate_directory_attributes(
            path=path,
            selector=request.selector,
            hostname=self.hostname,
            port=self.port,
            admin_name=self.admin_name,
            admin_email=self.admin_email,
        )

        # Combine all attribute blocks
        combined = "\n".join(attrs.to_string() for attrs in attrs_list)

        return GopherResponse(
            raw_body=combined.encode("utf-8"),
            is_directory=False,
        )

    def _is_safe_path(self, file_path: Path) -> bool:
        """Check if a file path is within the document root.

        Args:
            file_path: The resolved file path to check.

        Returns:
            True if the path is safe, False otherwise.
        """
        try:
            file_path.relative_to(self.document_root)
            return True
        except ValueError:
            return False


class ErrorHandler(RequestHandler):
    """Handler that returns error responses.

    Useful for handling 404 Not Found and other error cases.

    Examples:
        >>> handler = ErrorHandler("Not found")
        >>> response = handler.handle(request)
    """

    def __init__(self, message: str = "Error") -> None:
        """Initialize the error handler.

        Args:
            message: The error message to return.
        """
        self.message = message

    def handle(self, request: GopherRequest) -> GopherResponse:
        """Return an error response.

        Args:
            request: The incoming request (ignored).

        Returns:
            A GopherResponse with an error item.
        """
        return GopherResponse(
            items=[create_error_item(self.message)],
            is_directory=True,
        )
