"""Download utilities for binary file handling.

This module provides utilities for saving binary Gopher responses to the
filesystem with appropriate filename extraction and directory resolution.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from urllib.parse import unquote


def extract_filename(selector: str, fallback: str = "download.bin") -> str:
    """Extract a filename from a Gopher selector path.

    Takes the last path component and sanitizes it for filesystem use.
    Falls back to a default name if selector is empty or ends with '/'.

    Args:
        selector: Gopher selector path (e.g., "/files/image.gif")
        fallback: Default filename if extraction fails

    Returns:
        Sanitized filename safe for filesystem use

    Examples:
        >>> extract_filename("/path/to/file.gif")
        'file.gif'
        >>> extract_filename("/directory/")
        'download.bin'
        >>> extract_filename("")
        'download.bin'
    """
    if not selector or selector.endswith("/"):
        return fallback

    # Get last path component
    parts = selector.rstrip("/").split("/")
    filename = parts[-1] if parts else fallback

    # URL decode (selectors may be percent-encoded)
    filename = unquote(filename)

    # Sanitize: remove dangerous characters
    # Keep alphanumeric, dots, dashes, underscores
    sanitized = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)

    # Ensure we have something
    return sanitized if sanitized else fallback


def get_download_dir() -> Path:
    """Get the user's download directory.

    Checks XDG_DOWNLOAD_DIR environment variable first, then falls back
    to ~/Downloads. Creates the directory if it doesn't exist.

    Returns:
        Path to the download directory

    Examples:
        >>> dir = get_download_dir()
        >>> dir.exists()
        True
    """
    # Try XDG_DOWNLOAD_DIR first
    xdg_download = os.environ.get("XDG_DOWNLOAD_DIR")
    if xdg_download:
        download_dir = Path(xdg_download)
    else:
        # Fall back to ~/Downloads
        download_dir = Path.home() / "Downloads"

    # Ensure directory exists
    download_dir.mkdir(parents=True, exist_ok=True)

    return download_dir


def save_binary(
    data: bytes,
    filename: str,
    directory: Path | None = None,
) -> Path:
    """Save binary data to a file.

    Writes binary content to the filesystem, silently overwriting if the
    file already exists. Uses default download directory if none specified.

    Args:
        data: Binary data to write
        filename: Name of the file to create
        directory: Directory to save in (defaults to get_download_dir())

    Returns:
        Path to the saved file

    Raises:
        OSError: If file cannot be written

    Examples:
        >>> path = save_binary(b"content", "test.bin", Path("/tmp"))
        >>> path.read_bytes()
        b'content'
    """
    if directory is None:
        directory = get_download_dir()

    # Ensure directory exists (in case custom directory was passed)
    directory.mkdir(parents=True, exist_ok=True)

    # Resolve final path
    file_path = directory / filename

    # Write binary data (overwrites silently)
    file_path.write_bytes(data)

    return file_path


def open_file(path: Path) -> None:
    """Open a file with the system's default application.

    Uses the appropriate command for the current platform:
    - Linux: xdg-open
    - macOS: open
    - Windows: start

    Args:
        path: Path to the file to open

    Raises:
        OSError: If the file cannot be opened (command not found or failed)

    Examples:
        >>> open_file(Path("/tmp/image.gif"))  # Opens in default image viewer
    """
    system = platform.system()

    if system == "Linux":
        cmd = ["xdg-open", str(path)]
    elif system == "Darwin":
        cmd = ["open", str(path)]
    elif system == "Windows":
        cmd = ["cmd", "/c", "start", "", str(path)]
    else:
        raise OSError(f"Unsupported platform: {system}")

    try:
        # Use subprocess.run with check=True to raise on failure
        # start_new_session=True prevents the child from receiving signals
        subprocess.run(cmd, check=True, start_new_session=True)
    except FileNotFoundError as e:
        raise OSError(f"Command not found: {cmd[0]}") from e
    except subprocess.CalledProcessError as e:
        raise OSError(f"Failed to open file: {e}") from e
