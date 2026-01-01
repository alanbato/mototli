"""Gopher+ attribute block generation for files.

This module provides functions for generating Gopher+ attribute blocks
(+INFO, +ADMIN, +VIEWS, +ABSTRACT) from file metadata.
"""

from datetime import datetime, timezone
from pathlib import Path

from ..protocol.attributes import GopherAttributes, ViewInfo
from ..protocol.constants import DEFAULT_PORT
from ..protocol.item_types import ItemType
from ..protocol.response import GopherItem
from ..utils.mime import get_item_type, get_mime_type


def generate_attributes(
    path: Path,
    selector: str,
    hostname: str,
    port: int = DEFAULT_PORT,
    admin_name: str | None = None,
    admin_email: str | None = None,
    abstract: str | None = None,
) -> GopherAttributes:
    """Generate Gopher+ attributes for a file or directory.

    Creates a GopherAttributes object with metadata about the specified
    file, suitable for responding to Gopher+ attribute requests.

    Args:
        path: Path to the file or directory.
        selector: The selector path for this item.
        hostname: Server hostname.
        port: Server port.
        admin_name: Administrator name for +ADMIN block.
        admin_email: Administrator email for +ADMIN block.
        abstract: Optional abstract/description for the item.

    Returns:
        A GopherAttributes object with metadata.

    Examples:
        >>> attrs = generate_attributes(
        ...     Path("/var/gopher/readme.txt"),
        ...     "/readme.txt",
        ...     "gopher.example.com",
        ... )
    """
    # Get file info
    item_type = get_item_type(path)
    display_text = path.name

    # Create +INFO item
    info = GopherItem(
        item_type=item_type,
        display_text=display_text,
        selector=selector,
        hostname=hostname,
        port=port,
        gopher_plus=True,
    )

    # Get modification date
    mod_date = None
    try:
        stat_info = path.stat()
        mod_date = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
    except OSError:
        pass

    # Generate views
    views: list[ViewInfo] = []
    if path.is_file():
        views = _generate_views(path)
    elif path.is_dir():
        views = [
            ViewInfo(
                mime_type="application/gopher-menu",
                size="variable",
            )
        ]

    # Read abstract from file if not provided
    if abstract is None and path.is_file():
        abstract = _read_abstract(path)

    return GopherAttributes(
        info=info,
        admin=admin_name,
        admin_email=admin_email,
        mod_date=mod_date,
        views=views,
        abstract=abstract,
    )


def _generate_views(path: Path) -> list[ViewInfo]:
    """Generate available views for a file.

    Args:
        path: Path to the file.

    Returns:
        A list of ViewInfo objects representing available views.
    """
    views: list[ViewInfo] = []

    try:
        stat_info = path.stat()
        size_bytes = stat_info.st_size
        size_str = _format_size(size_bytes)
    except OSError:
        size_bytes = None
        size_str = None

    # Primary view based on file type
    mime_type = get_mime_type(path)
    views.append(
        ViewInfo(
            mime_type=mime_type,
            size=size_str,
            size_bytes=size_bytes,
        )
    )

    # Add alternative views for certain types
    if mime_type.startswith("text/"):
        # Text files can be viewed as plain text
        if mime_type != "text/plain":
            views.append(
                ViewInfo(
                    mime_type="text/plain",
                    size=size_str,
                    size_bytes=size_bytes,
                )
            )

    return views


def _format_size(size_bytes: int) -> str:
    """Format a file size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        A human-readable size string (e.g., "10k", "1.5M").
    """
    if size_bytes < 1024:
        return str(size_bytes)
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f}k"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}M"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}G"


def _read_abstract(path: Path, max_lines: int = 5, max_chars: int = 500) -> str | None:
    """Try to read an abstract from the beginning of a text file.

    Reads the first few lines of a file to use as an abstract/description.

    Args:
        path: Path to the file.
        max_lines: Maximum number of lines to read.
        max_chars: Maximum total characters to return.

    Returns:
        The abstract text, or None if the file is not readable as text.
    """
    # Only attempt for text-like files
    item_type = get_item_type(path)
    if item_type not in (ItemType.TEXT, ItemType.HTML):
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            lines: list[str] = []
            total_chars = 0

            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break

                # Strip and skip empty lines at the beginning
                stripped = line.strip()
                if not lines and not stripped:
                    continue

                lines.append(stripped)
                total_chars += len(stripped)

                if total_chars >= max_chars:
                    break

            if lines:
                abstract = "\n".join(lines)
                if len(abstract) > max_chars:
                    abstract = abstract[: max_chars - 3] + "..."
                return abstract

    except (OSError, UnicodeDecodeError):
        pass

    return None


def generate_directory_attributes(
    path: Path,
    selector: str,
    hostname: str,
    port: int = DEFAULT_PORT,
    admin_name: str | None = None,
    admin_email: str | None = None,
) -> list[GopherAttributes]:
    """Generate Gopher+ attributes for all items in a directory.

    Creates attribute blocks for each file and subdirectory in the
    specified directory. Used for Gopher+ directory attribute requests.

    Args:
        path: Path to the directory.
        selector: The base selector path for items.
        hostname: Server hostname.
        port: Server port.
        admin_name: Administrator name for +ADMIN blocks.
        admin_email: Administrator email for +ADMIN blocks.

    Returns:
        A list of GopherAttributes objects, one for each item.

    Raises:
        ValueError: If the path is not a directory.
    """
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    attributes: list[GopherAttributes] = []

    # Normalize selector base
    if not selector.startswith("/"):
        selector = "/" + selector
    if not selector.endswith("/") and selector != "/":
        selector = selector + "/"

    try:
        for entry in sorted(path.iterdir(), key=lambda x: x.name.lower()):
            # Skip hidden files
            if entry.name.startswith("."):
                continue

            # Build item selector
            if selector == "/":
                item_selector = "/" + entry.name
            else:
                item_selector = selector + entry.name

            attrs = generate_attributes(
                path=entry,
                selector=item_selector,
                hostname=hostname,
                port=port,
                admin_name=admin_name,
                admin_email=admin_email,
            )
            attributes.append(attrs)

    except PermissionError:
        pass

    return attributes
