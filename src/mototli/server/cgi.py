"""CGI script execution for Gopher server.

This module provides the CGIHandler for executing CGI scripts
and returning their output as Gopher responses.
"""

import asyncio
import os
import subprocess
from pathlib import Path

from ..protocol.constants import DEFAULT_PORT
from ..protocol.item_types import ItemType
from ..protocol.request import GopherRequest
from ..protocol.response import GopherItem, GopherResponse, create_error_item
from .handler import RequestHandler


class CGIHandler(RequestHandler):
    """Handler for executing CGI scripts.

    This handler executes CGI scripts and returns their output as Gopher
    responses. Scripts can be identified by file extension (e.g., .cgi)
    or by being located in a CGI directory (e.g., cgi-bin/).

    The handler sets up standard CGI environment variables plus
    Gopher-specific variables like SELECTOR and GOPHER_PLUS.

    Attributes:
        document_root: Path to the document root.
        hostname: Server hostname for environment variables.
        port: Server port for environment variables.
        cgi_extensions: File extensions that indicate CGI scripts.
        cgi_directories: Directory names that contain CGI scripts.
        timeout: Timeout for CGI script execution in seconds.
        gopher_plus: Whether Gopher+ is enabled.

    Examples:
        >>> handler = CGIHandler(
        ...     document_root=Path("/var/gopher"),
        ...     hostname="gopher.example.com",
        ...     cgi_extensions=[".cgi", ".sh"],
        ...     cgi_directories=["cgi-bin"],
        ... )
    """

    def __init__(
        self,
        document_root: Path | str,
        hostname: str,
        port: int = DEFAULT_PORT,
        cgi_extensions: list[str] | None = None,
        cgi_directories: list[str] | None = None,
        timeout: float = 30.0,
        gopher_plus: bool = True,
    ) -> None:
        """Initialize the CGI handler.

        Args:
            document_root: Path to the document root.
            hostname: Server hostname for environment variables.
            port: Server port for environment variables.
            cgi_extensions: File extensions that indicate CGI scripts.
            cgi_directories: Directory names that contain CGI scripts.
            timeout: Timeout for CGI script execution in seconds.
            gopher_plus: Whether Gopher+ is enabled.
        """
        self.document_root = Path(document_root).resolve()
        self.hostname = hostname
        self.port = port
        self.cgi_extensions = cgi_extensions or [".cgi", ".sh", ".py", ".pl"]
        self.cgi_directories = cgi_directories or ["cgi-bin"]
        self.timeout = timeout
        self.gopher_plus = gopher_plus

    def handle(self, request: GopherRequest) -> GopherResponse:
        """Handle a request by executing the CGI script.

        This method runs synchronously but calls an async helper
        to execute the CGI script.

        Args:
            request: The incoming request.

        Returns:
            A GopherResponse with the CGI script output.
        """
        # Get the requested path
        selector = request.selector.lstrip("/")
        if not selector:
            return GopherResponse(
                items=[create_error_item("Invalid CGI request")],
                is_directory=True,
            )

        # Construct the script path
        script_path = (self.document_root / selector).resolve()

        # Path traversal protection
        if not self._is_safe_path(script_path):
            return GopherResponse(
                items=[create_error_item("Not found")],
                is_directory=True,
            )

        # Check if file exists and is executable
        if not script_path.exists():
            return GopherResponse(
                items=[create_error_item("Not found")],
                is_directory=True,
            )

        if not script_path.is_file():
            return GopherResponse(
                items=[create_error_item("Not a file")],
                is_directory=True,
            )

        if not os.access(script_path, os.X_OK):
            return GopherResponse(
                items=[create_error_item("Script not executable")],
                is_directory=True,
            )

        # Verify this is a CGI script
        if not self._is_cgi_script(script_path, selector):
            return GopherResponse(
                items=[create_error_item("Not a CGI script")],
                is_directory=True,
            )

        # Execute the script
        try:
            return self._execute_cgi_sync(script_path, request)
        except Exception as e:
            return GopherResponse(
                items=[create_error_item(f"CGI error: {e}")],
                is_directory=True,
            )

    def _execute_cgi_sync(
        self, script_path: Path, request: GopherRequest
    ) -> GopherResponse:
        """Execute a CGI script synchronously.

        Args:
            script_path: Path to the CGI script.
            request: The incoming request.

        Returns:
            A GopherResponse with the script output.
        """
        # Build environment variables
        env = self._build_cgi_env(script_path, request)

        try:
            # Execute the script
            result = subprocess.run(
                [str(script_path)],
                capture_output=True,
                timeout=self.timeout,
                env=env,
                cwd=script_path.parent,
            )

            stdout = result.stdout
            stderr = result.stderr

            # Check for errors
            if result.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                if not error_msg:
                    error_msg = f"Script exited with code {result.returncode}"
                return GopherResponse(
                    items=[create_error_item(f"CGI error: {error_msg}")],
                    is_directory=True,
                )

            # Parse the output
            return self._parse_cgi_output(stdout)

        except subprocess.TimeoutExpired:
            return GopherResponse(
                items=[create_error_item("CGI script timeout")],
                is_directory=True,
            )

        except PermissionError:
            return GopherResponse(
                items=[create_error_item("Permission denied")],
                is_directory=True,
            )

        except OSError as e:
            return GopherResponse(
                items=[create_error_item(f"Cannot execute script: {e}")],
                is_directory=True,
            )

    async def execute_cgi_async(
        self, script_path: Path, request: GopherRequest
    ) -> GopherResponse:
        """Execute a CGI script asynchronously.

        This method uses asyncio subprocess for non-blocking execution.

        Args:
            script_path: Path to the CGI script.
            request: The incoming request.

        Returns:
            A GopherResponse with the script output.
        """
        # Build environment variables
        env = self._build_cgi_env(script_path, request)

        try:
            # Execute the script
            proc = await asyncio.create_subprocess_exec(
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=script_path.parent,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return GopherResponse(
                    items=[create_error_item("CGI script timeout")],
                    is_directory=True,
                )

            # Check for errors
            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                if not error_msg:
                    error_msg = f"Script exited with code {proc.returncode}"
                return GopherResponse(
                    items=[create_error_item(f"CGI error: {error_msg}")],
                    is_directory=True,
                )

            # Parse the output
            return self._parse_cgi_output(stdout)

        except PermissionError:
            return GopherResponse(
                items=[create_error_item("Permission denied")],
                is_directory=True,
            )

        except OSError as e:
            return GopherResponse(
                items=[create_error_item(f"Cannot execute script: {e}")],
                is_directory=True,
            )

    def _build_cgi_env(self, script_path: Path, request: GopherRequest) -> dict[str, str]:
        """Build CGI environment variables.

        Creates environment variables following RFC 3875 plus
        Gopher-specific extensions.

        Args:
            script_path: Path to the CGI script.
            request: The incoming request.

        Returns:
            Dictionary of environment variables.
        """
        env = os.environ.copy()

        # Standard CGI variables
        env["GATEWAY_INTERFACE"] = "CGI/1.1"
        env["SERVER_PROTOCOL"] = "GOPHER"
        env["SERVER_SOFTWARE"] = "Mototli/1.0"
        env["SERVER_NAME"] = self.hostname
        env["SERVER_PORT"] = str(self.port)
        env["REQUEST_METHOD"] = "GET"
        env["SCRIPT_NAME"] = "/" + str(script_path.relative_to(self.document_root))
        env["SCRIPT_FILENAME"] = str(script_path)
        env["DOCUMENT_ROOT"] = str(self.document_root)

        # Request-specific variables
        env["SELECTOR"] = request.selector
        env["PATH_INFO"] = request.selector
        env["QUERY_STRING"] = request.search_query or ""

        # Client information
        if request.client_ip:
            env["REMOTE_ADDR"] = request.client_ip
            env["REMOTE_HOST"] = request.client_ip

        # Gopher+ specific variables
        if request.is_gopher_plus:
            env["GOPHER_PLUS"] = "1"
            env["REQUEST_TYPE"] = request.request_type.value
            if request.view_type:
                env["VIEW_TYPE"] = request.view_type
        else:
            env["GOPHER_PLUS"] = "0"

        return env

    def _parse_cgi_output(self, output: bytes) -> GopherResponse:
        """Parse CGI script output.

        Determines if the output is a directory listing or raw content.

        Args:
            output: The raw CGI output bytes.

        Returns:
            A GopherResponse with the parsed output.
        """
        # Try to decode as UTF-8
        try:
            text = output.decode("utf-8")
        except UnicodeDecodeError:
            # Binary content
            return GopherResponse(
                raw_body=output,
                is_directory=False,
            )

        # Check if this looks like a directory listing
        # (lines starting with item type characters and containing tabs)
        lines = text.splitlines()
        if self._looks_like_directory(lines):
            return self._parse_as_directory(lines)

        # Return as raw content
        return GopherResponse(
            raw_body=output,
            is_directory=False,
        )

    def _looks_like_directory(self, lines: list[str]) -> bool:
        """Check if output looks like a directory listing.

        Args:
            lines: List of output lines.

        Returns:
            True if the output appears to be a directory listing.
        """
        if not lines:
            return False

        # Check if most lines have the directory format
        directory_lines = 0
        for line in lines[:10]:  # Check first 10 lines
            if not line:
                continue
            # Directory lines start with a type char and contain tabs
            if len(line) > 1 and "\t" in line:
                try:
                    ItemType.from_char(line[0])
                    directory_lines += 1
                except ValueError:
                    # 'i' is a common info type that should also work
                    if line[0] == "i":
                        directory_lines += 1

        return directory_lines > len(lines[:10]) // 2

    def _parse_as_directory(self, lines: list[str]) -> GopherResponse:
        """Parse CGI output as a directory listing.

        Args:
            lines: List of output lines.

        Returns:
            A GopherResponse with parsed directory items.
        """
        items: list[GopherItem] = []

        for line in lines:
            if not line:
                continue

            # Skip terminator
            if line == ".":
                continue

            # Parse the line
            parts = line.split("\t")
            if len(parts) < 2:
                # Treat as info line
                items.append(
                    GopherItem(
                        item_type=ItemType.INFO,
                        display_text=line,
                        selector="",
                        hostname=self.hostname,
                        port=self.port,
                    )
                )
                continue

            # First character is type
            type_char = parts[0][0] if parts[0] else "i"
            display_text = parts[0][1:] if len(parts[0]) > 1 else ""

            try:
                item_type = ItemType.from_char(type_char)
            except ValueError:
                item_type = ItemType.INFO

            selector = parts[1] if len(parts) > 1 else ""
            hostname = parts[2] if len(parts) > 2 else self.hostname

            try:
                port = int(parts[3].rstrip("+")) if len(parts) > 3 else self.port
            except ValueError:
                port = self.port

            gopher_plus = len(parts) > 3 and parts[3].endswith("+")

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

        return GopherResponse(items=items, is_directory=True)

    def _is_cgi_script(self, path: Path, selector: str) -> bool:
        """Check if a path is a CGI script.

        Args:
            path: Path to check.
            selector: The selector path.

        Returns:
            True if the path is a CGI script.
        """
        # Check extension
        if path.suffix.lower() in self.cgi_extensions:
            return True

        # Check if in a CGI directory
        selector_parts = selector.strip("/").split("/")
        for part in selector_parts:
            if part in self.cgi_directories:
                return True

        return False

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

    def can_handle(self, selector: str) -> bool:
        """Check if this handler can handle a selector.

        This is useful for routing decisions.

        Args:
            selector: The selector to check.

        Returns:
            True if this handler can handle the selector.
        """
        # Check if in a CGI directory
        selector_parts = selector.strip("/").split("/")
        for part in selector_parts:
            if part in self.cgi_directories:
                return True

        # Check extension
        path = Path(selector)
        if path.suffix.lower() in self.cgi_extensions:
            return True

        return False
