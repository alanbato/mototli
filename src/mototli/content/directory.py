"""Directory listing generation for Gopher server.

This module provides functions for generating Gopher directory listings
from filesystem directories.
"""

from pathlib import Path

from ..protocol.constants import DEFAULT_PORT
from ..protocol.item_types import ItemType
from ..protocol.response import GopherItem, create_info_item
from ..utils.mime import get_item_type


def generate_directory_listing(
    path: Path,
    selector_base: str,
    hostname: str,
    port: int = DEFAULT_PORT,
    gopher_plus: bool = True,
    show_hidden: bool = False,
) -> list[GopherItem]:
    """Generate a Gopher directory listing from a filesystem path.

    Creates a list of GopherItem objects representing the contents of
    a directory, suitable for serialization as a Gopher menu.

    Args:
        path: Path to the directory to list.
        selector_base: The base selector path for items (e.g., "/files").
        hostname: Server hostname for the items.
        port: Server port for the items.
        gopher_plus: Whether to indicate Gopher+ support.
        show_hidden: Whether to show hidden files (starting with '.').

    Returns:
        A list of GopherItem objects representing the directory contents.

    Raises:
        ValueError: If the path is not a directory.

    Examples:
        >>> items = generate_directory_listing(
        ...     Path("/var/gopher"),
        ...     "/",
        ...     "gopher.example.com",
        ... )
    """
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    items: list[GopherItem] = []

    # Normalize selector base
    if not selector_base.startswith("/"):
        selector_base = "/" + selector_base
    if not selector_base.endswith("/") and selector_base != "/":
        selector_base = selector_base + "/"
    if selector_base == "//":
        selector_base = "/"

    # Add parent directory link if not at root
    if selector_base != "/":
        parent_selector = "/".join(selector_base.rstrip("/").split("/")[:-1])
        if not parent_selector:
            parent_selector = "/"
        items.append(
            GopherItem(
                item_type=ItemType.DIRECTORY,
                display_text="..",
                selector=parent_selector,
                hostname=hostname,
                port=port,
                gopher_plus=gopher_plus,
            )
        )

    # Get directory entries
    entries: list[tuple[bool, str, Path]] = []
    try:
        for entry in path.iterdir():
            # Skip hidden files unless explicitly requested
            if not show_hidden and entry.name.startswith("."):
                continue

            # Store as (is_dir, name, path) for sorting
            entries.append((entry.is_dir(), entry.name.lower(), entry))
    except PermissionError:
        items.append(create_info_item("Permission denied"))
        return items

    # Sort: directories first, then alphabetically by name
    entries.sort(key=lambda x: (not x[0], x[1]))

    # Create items for each entry
    for _, _, entry_path in entries:
        item_type = get_item_type(entry_path)

        # Build selector
        if selector_base == "/":
            selector = "/" + entry_path.name
        else:
            selector = selector_base + entry_path.name

        # Add trailing slash for directories in display
        display_text = entry_path.name
        if entry_path.is_dir():
            display_text += "/"

        items.append(
            GopherItem(
                item_type=item_type,
                display_text=display_text,
                selector=selector,
                hostname=hostname,
                port=port,
                gopher_plus=gopher_plus,
            )
        )

    return items


def generate_welcome_header(
    title: str,
    hostname: str,
    description: str | None = None,
) -> list[GopherItem]:
    """Generate a welcome header for a directory listing.

    Creates informational items that appear at the top of a directory
    listing, providing a title and optional description.

    Args:
        title: The title to display.
        hostname: Hostname for the info items.
        description: Optional description text.

    Returns:
        A list of informational GopherItem objects.

    Examples:
        >>> header = generate_welcome_header(
        ...     "Welcome to My Gopher Server",
        ...     "gopher.example.com",
        ...     "This is a test server.",
        ... )
    """
    items: list[GopherItem] = []

    # Add title
    items.append(create_info_item(title, hostname))

    # Add description if provided
    if description:
        items.append(create_info_item("", hostname))  # Blank line
        for line in description.split("\n"):
            items.append(create_info_item(line, hostname))

    # Add separator
    items.append(create_info_item("", hostname))
    items.append(create_info_item("-" * 40, hostname))
    items.append(create_info_item("", hostname))

    return items
