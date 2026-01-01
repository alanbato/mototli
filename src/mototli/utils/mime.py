"""MIME type detection and Gopher item type mapping.

This module provides utilities for detecting MIME types from file extensions
and mapping them to appropriate Gopher item types.
"""

from pathlib import Path

from ..protocol.item_types import ItemType

# File extension to MIME type mapping
EXTENSION_TO_MIME: dict[str, str] = {
    # Text files
    ".txt": "text/plain",
    ".text": "text/plain",
    ".md": "text/markdown",
    ".rst": "text/x-rst",
    ".log": "text/plain",
    # HTML
    ".html": "text/html",
    ".htm": "text/html",
    ".xhtml": "application/xhtml+xml",
    # Source code
    ".py": "text/x-python",
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".xml": "application/xml",
    ".yaml": "text/yaml",
    ".yml": "text/yaml",
    ".toml": "text/toml",
    ".c": "text/x-c",
    ".cpp": "text/x-c++",
    ".h": "text/x-c",
    ".java": "text/x-java",
    ".rb": "text/x-ruby",
    ".rs": "text/x-rust",
    ".go": "text/x-go",
    ".sh": "text/x-shellscript",
    # Images
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".bmp": "image/bmp",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    # Audio
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
    # Video
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".rtf": "application/rtf",
    # Archives
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".bz2": "application/x-bzip2",
    ".xz": "application/x-xz",
    ".7z": "application/x-7z-compressed",
    ".rar": "application/vnd.rar",
    # Gopher-specific
    ".gph": "text/gopher",
    ".gophermap": "text/gopher",
}

# File extension to Gopher item type mapping
EXTENSION_TO_ITEM_TYPE: dict[str, ItemType] = {
    # Text files
    ".txt": ItemType.TEXT,
    ".text": ItemType.TEXT,
    ".md": ItemType.TEXT,
    ".rst": ItemType.TEXT,
    ".log": ItemType.TEXT,
    ".py": ItemType.TEXT,
    ".js": ItemType.TEXT,
    ".css": ItemType.TEXT,
    ".json": ItemType.TEXT,
    ".xml": ItemType.TEXT,
    ".yaml": ItemType.TEXT,
    ".yml": ItemType.TEXT,
    ".toml": ItemType.TEXT,
    ".c": ItemType.TEXT,
    ".cpp": ItemType.TEXT,
    ".h": ItemType.TEXT,
    ".java": ItemType.TEXT,
    ".rb": ItemType.TEXT,
    ".rs": ItemType.TEXT,
    ".go": ItemType.TEXT,
    ".sh": ItemType.TEXT,
    # Gopher-specific text
    ".gph": ItemType.TEXT,
    ".gophermap": ItemType.TEXT,
    # HTML
    ".html": ItemType.HTML,
    ".htm": ItemType.HTML,
    ".xhtml": ItemType.HTML,
    # Images
    ".gif": ItemType.GIF,
    ".jpg": ItemType.IMAGE,
    ".jpeg": ItemType.IMAGE,
    ".png": ItemType.PNG,
    ".bmp": ItemType.BITMAP,
    ".ico": ItemType.IMAGE,
    ".svg": ItemType.IMAGE,
    ".webp": ItemType.IMAGE,
    # Audio
    ".wav": ItemType.AUDIO,
    ".mp3": ItemType.AUDIO,
    ".ogg": ItemType.AUDIO,
    ".flac": ItemType.AUDIO,
    ".aac": ItemType.AUDIO,
    ".m4a": ItemType.AUDIO,
    # Video
    ".mp4": ItemType.MOVIE,
    ".webm": ItemType.MOVIE,
    ".avi": ItemType.MOVIE,
    ".mov": ItemType.MOVIE,
    ".mkv": ItemType.MOVIE,
    # Documents
    ".pdf": ItemType.DOC,
    ".doc": ItemType.DOC,
    ".docx": ItemType.DOC,
    ".odt": ItemType.DOC,
    ".rtf": ItemType.DOC,
    # Archives/Binary
    ".zip": ItemType.DOS_BINARY,
    ".tar": ItemType.BINARY,
    ".gz": ItemType.BINARY,
    ".bz2": ItemType.BINARY,
    ".xz": ItemType.BINARY,
    ".7z": ItemType.DOS_BINARY,
    ".rar": ItemType.DOS_BINARY,
    ".exe": ItemType.DOS_BINARY,
    ".bin": ItemType.BINARY,
}


def get_mime_type(path: Path) -> str:
    """Get the MIME type for a file based on its extension.

    Args:
        path: Path to the file.

    Returns:
        The MIME type string, or "application/octet-stream" if unknown.

    Examples:
        >>> get_mime_type(Path("file.txt"))
        'text/plain'
        >>> get_mime_type(Path("image.gif"))
        'image/gif'
    """
    suffix = path.suffix.lower()
    return EXTENSION_TO_MIME.get(suffix, "application/octet-stream")


def get_item_type(path: Path) -> ItemType:
    """Get the Gopher item type for a file based on its extension.

    Args:
        path: Path to the file.

    Returns:
        The appropriate ItemType for the file.

    Examples:
        >>> get_item_type(Path("file.txt"))
        <ItemType.TEXT: '0'>
        >>> get_item_type(Path("image.gif"))
        <ItemType.GIF: 'g'>
    """
    if path.is_dir():
        return ItemType.DIRECTORY

    suffix = path.suffix.lower()
    return EXTENSION_TO_ITEM_TYPE.get(suffix, ItemType.BINARY)


def get_item_type_from_selector(selector: str) -> ItemType | None:
    """Get the Gopher item type from a selector's file extension.

    Args:
        selector: The Gopher selector path (e.g., "/files/image.gif").

    Returns:
        The appropriate ItemType if extension is recognized, None otherwise.

    Examples:
        >>> get_item_type_from_selector("/files/image.gif")
        <ItemType.GIF: 'g'>
        >>> get_item_type_from_selector("/directory/")
        None
        >>> get_item_type_from_selector("/unknown.xyz")
        None
    """
    if not selector or selector.endswith("/"):
        return None

    # Extract the last path component
    parts = selector.rstrip("/").split("/")
    filename = parts[-1] if parts else ""

    if not filename or "." not in filename:
        return None

    # Get the extension
    suffix = "." + filename.rsplit(".", 1)[-1].lower()

    return EXTENSION_TO_ITEM_TYPE.get(suffix)


def get_item_type_from_mime(mime_type: str) -> ItemType:
    """Get the Gopher item type for a MIME type.

    Args:
        mime_type: The MIME type string.

    Returns:
        The appropriate ItemType for the MIME type.

    Examples:
        >>> get_item_type_from_mime("text/plain")
        <ItemType.TEXT: '0'>
        >>> get_item_type_from_mime("image/gif")
        <ItemType.GIF: 'g'>
    """
    # Normalize MIME type
    mime_type = mime_type.lower().split(";")[0].strip()

    # Text types
    if mime_type.startswith("text/"):
        if mime_type == "text/html":
            return ItemType.HTML
        return ItemType.TEXT

    # Images
    if mime_type.startswith("image/"):
        if mime_type == "image/gif":
            return ItemType.GIF
        if mime_type == "image/png":
            return ItemType.PNG
        if mime_type == "image/bmp":
            return ItemType.BITMAP
        return ItemType.IMAGE

    # Audio
    if mime_type.startswith("audio/"):
        return ItemType.AUDIO

    # Video
    if mime_type.startswith("video/"):
        return ItemType.MOVIE

    # Documents
    if mime_type in ("application/pdf", "application/msword", "application/rtf"):
        return ItemType.DOC
    if mime_type.startswith("application/vnd."):
        return ItemType.DOC

    # Archives
    archive_types = (
        "application/zip",
        "application/x-7z-compressed",
        "application/vnd.rar",
    )
    if mime_type in archive_types:
        return ItemType.DOS_BINARY
    if mime_type.startswith("application/x-"):
        return ItemType.BINARY

    # Default to binary
    return ItemType.BINARY
