"""Server configuration for Mototli Gopher server.

This module provides the ServerConfig dataclass for configuring the Gopher server.
Configuration can be loaded from TOML files or created programmatically.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..protocol.constants import DEFAULT_PORT, REQUEST_TIMEOUT


@dataclass
class ServerConfig:
    """Configuration for the Gopher server.

    Attributes:
        host: The host address to bind to.
        port: The port to listen on (default 70).
        document_root: Path to the directory containing files to serve.
        hostname: Public hostname for generating menu items. If None, uses host.
        enable_directory_listing: Whether to generate directory listings.
        default_indices: List of index filenames to try for directory requests.
        cgi_extensions: File extensions that indicate CGI scripts.
        cgi_directories: Directory names that contain CGI scripts.
        max_file_size: Maximum file size to serve in bytes.
        request_timeout: Timeout for receiving requests in seconds.
        cgi_timeout: Timeout for CGI script execution in seconds.
        gopher_plus: Whether Gopher+ is enabled.
        admin_name: Administrator name for Gopher+ ADMIN block.
        admin_email: Administrator email for Gopher+ ADMIN block.

    Examples:
        >>> config = ServerConfig(
        ...     host="localhost",
        ...     port=70,
        ...     document_root=Path("/var/gopher"),
        ... )
    """

    host: str = "localhost"
    port: int = DEFAULT_PORT
    document_root: Path = field(default_factory=lambda: Path("."))
    hostname: str | None = None
    enable_directory_listing: bool = True
    default_indices: list[str] = field(
        default_factory=lambda: ["index.gph", "gophermap", "index.txt"]
    )
    cgi_extensions: list[str] = field(
        default_factory=lambda: [".cgi", ".sh", ".py", ".pl"]
    )
    cgi_directories: list[str] = field(default_factory=lambda: ["cgi-bin"])
    max_file_size: int = 100 * 1024 * 1024  # 100 MiB
    request_timeout: float = REQUEST_TIMEOUT
    cgi_timeout: float = 30.0
    gopher_plus: bool = True
    admin_name: str | None = None
    admin_email: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize configuration after initialization."""
        # Ensure document_root is a Path
        if isinstance(self.document_root, str):
            self.document_root = Path(self.document_root)

        # Resolve to absolute path
        self.document_root = self.document_root.resolve()

        # Use host as hostname if not specified
        if self.hostname is None:
            self.hostname = self.host

    def validate(self) -> None:
        """Validate the configuration.

        Raises:
            ValueError: If the configuration is invalid.
        """
        # Check document root exists
        if not self.document_root.exists():
            raise ValueError(f"Document root does not exist: {self.document_root}")
        if not self.document_root.is_dir():
            raise ValueError(f"Document root is not a directory: {self.document_root}")

        # Check port is valid
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got: {self.port}")

        # Check timeouts are positive
        if self.request_timeout <= 0:
            raise ValueError(
                f"Request timeout must be positive, got: {self.request_timeout}"
            )
        if self.cgi_timeout <= 0:
            raise ValueError(f"CGI timeout must be positive, got: {self.cgi_timeout}")

        # Check file size limit is positive
        if self.max_file_size <= 0:
            raise ValueError(f"Max file size must be positive, got: {self.max_file_size}")

    @classmethod
    def from_toml(cls, path: Path | str) -> "ServerConfig":
        """Load configuration from a TOML file.

        Args:
            path: Path to the TOML configuration file.

        Returns:
            A ServerConfig instance with values from the file.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            ValueError: If the config file is invalid.

        Examples:
            >>> config = ServerConfig.from_toml("config.toml")
        """
        import sys

        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("rb") as f:
            data = tomllib.load(f)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "ServerConfig":
        """Create a ServerConfig from a dictionary.

        Args:
            data: Dictionary with configuration values.

        Returns:
            A ServerConfig instance.
        """
        server = data.get("server", {})
        handlers = data.get("handlers", {})
        gopher_plus = data.get("gopher_plus", {})
        limits = data.get("limits", {})

        # Extract document_root and convert to Path
        document_root = server.get("document_root", ".")
        if isinstance(document_root, str):
            document_root = Path(document_root)

        return cls(
            host=server.get("host", "localhost"),
            port=server.get("port", DEFAULT_PORT),
            document_root=document_root,
            hostname=server.get("hostname"),
            enable_directory_listing=handlers.get("enable_directory_listing", True),
            default_indices=handlers.get(
                "default_indices", ["index.gph", "gophermap", "index.txt"]
            ),
            cgi_extensions=handlers.get("cgi_extensions", [".cgi", ".sh", ".py", ".pl"]),
            cgi_directories=handlers.get("cgi_directories", ["cgi-bin"]),
            max_file_size=limits.get("max_file_size", 100 * 1024 * 1024),
            request_timeout=limits.get("request_timeout", REQUEST_TIMEOUT),
            cgi_timeout=limits.get("cgi_timeout", 30.0),
            gopher_plus=gopher_plus.get("enabled", True),
            admin_name=gopher_plus.get("admin_name"),
            admin_email=gopher_plus.get("admin_email"),
        )

    def to_toml(self) -> str:
        """Serialize the configuration to a TOML string.

        Returns:
            The configuration as a TOML-formatted string.
        """
        lines = [
            "# Mototli Gopher Server Configuration",
            "",
            "[server]",
            f'host = "{self.host}"',
            f"port = {self.port}",
            f'document_root = "{self.document_root}"',
        ]

        if self.hostname:
            lines.append(f'hostname = "{self.hostname}"')

        lines.extend(
            [
                "",
                "[handlers]",
                f"enable_directory_listing = {str(self.enable_directory_listing).lower()}",  # noqa: E501
                f"default_indices = {self.default_indices!r}",
                f"cgi_extensions = {self.cgi_extensions!r}",
                f"cgi_directories = {self.cgi_directories!r}",
                "",
                "[gopher_plus]",
                f"enabled = {str(self.gopher_plus).lower()}",
            ]
        )

        if self.admin_name:
            lines.append(f'admin_name = "{self.admin_name}"')
        if self.admin_email:
            lines.append(f'admin_email = "{self.admin_email}"')

        lines.extend(
            [
                "",
                "[limits]",
                f"max_file_size = {self.max_file_size}",
                f"request_timeout = {self.request_timeout}",
                f"cgi_timeout = {self.cgi_timeout}",
            ]
        )

        return "\n".join(lines) + "\n"

    @property
    def public_hostname(self) -> str:
        """Get the public hostname for menu items."""
        return self.hostname or self.host

    @property
    def public_port(self) -> int:
        """Get the public port for menu items."""
        return self.port
