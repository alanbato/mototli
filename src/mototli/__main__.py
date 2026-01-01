"""Mototli Gopher Protocol Client and Server CLI.

This module provides a command-line interface for the Mototli Gopher client
and server.
"""

import asyncio
import sys
from importlib.metadata import version as get_version
from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from .client.session import GopherClient
from .protocol.constants import DEFAULT_PORT, REQUEST_TIMEOUT
from .protocol.item_types import ItemType
from .protocol.response import GopherResponse
from .utils.downloads import extract_filename, open_file, save_binary
from .utils.mime import get_item_type_from_selector

# Create console instances
console = Console()
error_console = Console(stderr=True, style="bold red")

app = typer.Typer(
    name="mototli",
    help="Mototli - A modern Gopher protocol client and server",
    add_completion=True,
    no_args_is_help=True,
)


def _handle_binary_output(
    response: GopherResponse,
    selector: str,
    force_stdout: bool = False,
    output_filename: str | None = None,
    download_dir: Path | None = None,
    open_after_save: bool = False,
) -> None:
    """Handle binary response output routing.

    Decides whether to save to file or write to stdout based on flags.
    Provides user feedback for file saves.

    Args:
        response: GopherResponse containing binary data
        selector: Original selector for filename extraction
        force_stdout: If True, write to stdout instead of saving
        output_filename: Override filename for saving
        download_dir: Override directory for saving
        open_after_save: If True, open the file with system default app
    """
    if not response.raw_body:
        error_console.print("[yellow]No binary content received[/]")
        return

    # Force to stdout if requested
    if force_stdout:
        sys.stdout.buffer.write(response.raw_body)
        return

    # Determine filename
    if output_filename:
        filename = output_filename
    else:
        filename = extract_filename(selector)

    # Save to filesystem
    try:
        saved_path = save_binary(
            response.raw_body,
            filename,
            directory=download_dir,
        )
        # User feedback
        console.print(f"[green]Saved to:[/] {saved_path}")
    except OSError as e:
        error_console.print(f"[red]Failed to save file:[/] {escape(str(e))}")
        raise typer.Exit(code=1) from e

    # Open file if requested
    if open_after_save:
        try:
            open_file(saved_path)
        except OSError as e:
            error_console.print(f"[red]Failed to open file:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e


def _format_directory(response: GopherResponse, verbose: bool = False) -> None:
    """Format and print a Gopher directory listing.

    Args:
        response: GopherResponse object containing directory items.
        verbose: Whether to show verbose output with full details.
    """
    if verbose:
        # Show as table
        table = Table(title="Gopher Directory", show_header=True)
        table.add_column("Type", style="cyan", width=4, justify="center")
        table.add_column("Description", style="white")
        table.add_column("Selector", style="dim")
        table.add_column("Host:Port", style="dim")

        for item in response.items:
            # Style based on item type
            type_str = item.item_type.value
            if item.item_type == ItemType.DIRECTORY:
                type_str = f"[bold blue]{type_str}[/]"
            elif item.item_type == ItemType.TEXT:
                type_str = f"[green]{type_str}[/]"
            elif item.item_type == ItemType.SEARCH:
                type_str = f"[yellow]{type_str}[/]"
            elif item.item_type == ItemType.ERROR:
                type_str = f"[red]{type_str}[/]"
            elif item.item_type == ItemType.INFO:
                type_str = f"[dim]{type_str}[/]"

            host_port = f"{item.hostname}:{item.port}" if item.hostname else ""

            table.add_row(
                type_str,
                escape(item.display_text) if item.display_text else "",
                escape(item.selector) if item.selector else "",
                host_port,
            )

        console.print(table)
    else:
        # Simple display with selectors
        # Calculate max display text length for alignment (excluding info items)
        max_len = 0
        for item in response.items:
            if not item.item_type.is_informational and item.display_text:
                max_len = max(max_len, len(item.display_text))
        # Cap at reasonable width and add padding
        max_len = min(max_len, 50)

        for item in response.items:
            type_char = item.item_type.value
            display = escape(item.display_text or "")
            selector = escape(item.selector or "")

            # Format selector display (dim, right-aligned)
            selector_display = f"[dim]{selector}[/]" if selector else ""

            # Color and format based on type
            if item.item_type == ItemType.DIRECTORY:
                padded = display.ljust(max_len)
                console.print(f"[bold blue][{type_char}][/] {padded}  {selector_display}")
            elif item.item_type == ItemType.TEXT:
                padded = display.ljust(max_len)
                console.print(f"[green][{type_char}][/] {padded}  {selector_display}")
            elif item.item_type == ItemType.SEARCH:
                padded = display.ljust(max_len)
                console.print(f"[yellow][{type_char}][/] {padded}  {selector_display}")
            elif item.item_type == ItemType.ERROR:
                padded = display.ljust(max_len)
                console.print(f"[red][{type_char}][/] {padded}  {selector_display}")
            elif item.item_type == ItemType.INFO:
                # Info items don't show selectors
                console.print(f"[dim]    {display}[/]")
            elif item.item_type.is_binary:
                padded = display.ljust(max_len)
                console.print(f"[magenta][{type_char}][/] {padded}  {selector_display}")
            elif item.item_type.is_external:
                padded = display.ljust(max_len)
                console.print(f"[cyan][{type_char}][/] {padded}  {selector_display}")
            else:
                padded = display.ljust(max_len)
                console.print(f"[{type_char}] {padded}  {selector_display}")


def _format_text(response: GopherResponse) -> None:
    """Format and print text content.

    Args:
        response: GopherResponse object containing text.
    """
    if response.text:
        console.print(response.text)
    else:
        error_console.print("[yellow]No content received[/]")


@app.command()
def get(
    host: str = typer.Argument(..., help="Gopher server hostname"),
    selector: str = typer.Argument("", help="Resource selector (path)"),
    port: int = typer.Option(
        DEFAULT_PORT,
        "--port",
        "-p",
        help="Server port",
    ),
    search: str | None = typer.Option(
        None,
        "--search",
        "-s",
        help="Search query (for type 7 servers)",
    ),
    item_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Item type (0=text, 1=dir, 9=binary). Auto-detects from extension.",
    ),
    timeout: float = typer.Option(
        REQUEST_TIMEOUT,
        "--timeout",
        help="Request timeout in seconds",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output with full details",
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        "-r",
        help="Output raw response without formatting",
    ),
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Force binary output to stdout (for piping)",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output filename for binary downloads",
    ),
    download_dir: Path | None = typer.Option(
        None,
        "--download-dir",
        "-d",
        help="Directory for binary downloads (default: ~/Downloads)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    open_file_flag: bool = typer.Option(
        False,
        "--open",
        help="Open saved file with system default application",
    ),
) -> None:
    """Get a Gopher resource and display it.

    Examples:

        # Browse the root directory of a Gopher server
        $ mototli get gopher.floodgap.com

        # Get a specific resource
        $ mototli get gopher.floodgap.com /overbite

        # Get a text file
        $ mototli get gopher.floodgap.com /gopher/welcome --type 0

        # Search on a Gopher server
        $ mototli get gopher.floodgap.com /v2/vs --type 7 --search "python"

        # Get with verbose output
        $ mototli get gopher.floodgap.com -v

        # Get raw output
        $ mototli get gopher.floodgap.com --raw

        # Download a binary file (type auto-detected from .gif extension)
        $ mototli get gopher.example.com /files/image.gif

        # Download with custom filename (type auto-detected from .zip)
        $ mototli get gopher.example.com /files/data.zip -o mydata.zip

        # Download to specific directory
        $ mototli get gopher.example.com /files/image.png -d /tmp

        # Pipe binary to stdout
        $ mototli get gopher.example.com /file.tar.gz --stdout | tar -xz

        # Download and open with default application
        $ mototli get gopher.example.com /files/image.gif --open
    """
    # Determine item type: explicit > auto-detect > default (directory)
    if item_type is not None:
        # User explicitly specified type
        try:
            expected_type = ItemType.from_char(item_type)
        except ValueError:
            error_console.print(f"[red]Error:[/] Unknown item type: {item_type}")
            error_console.print("Common types: 0=text, 1=directory, 7=search, 9=binary")
            raise typer.Exit(code=1) from None
    else:
        # Try to auto-detect from selector extension
        detected_type = get_item_type_from_selector(selector)
        if detected_type is not None:
            expected_type = detected_type
        else:
            # Default to directory for root/unknown selectors
            expected_type = ItemType.DIRECTORY

    async def _get() -> None:
        try:
            async with GopherClient(timeout=timeout) as client:
                response = await client.get(
                    host=host,
                    selector=selector,
                    port=port,
                    search_query=search,
                    item_type=expected_type,
                )

                # Format and display response
                if raw:
                    # Raw mode - always output bytes to stdout
                    if response.raw_body:
                        sys.stdout.buffer.write(response.raw_body)
                    elif response.items:
                        raw_output = response.to_bytes().decode("utf-8", errors="replace")
                        console.print(raw_output)
                elif response.is_directory:
                    # Directory listing
                    _format_directory(response, verbose=verbose)
                elif expected_type.is_binary:
                    # Binary content - save to file or stdout
                    _handle_binary_output(
                        response=response,
                        selector=selector,
                        force_stdout=stdout,
                        output_filename=output,
                        download_dir=download_dir,
                        open_after_save=open_file_flag,
                    )
                else:
                    # Text content - display
                    _format_text(response)

        except TimeoutError as e:
            error_console.print(f"[red]Timeout:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e
        except ConnectionError as e:
            error_console.print(f"[red]Connection error:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e
        except Exception as e:
            error_console.print(f"[red]Error:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e

    # Run the async function
    asyncio.run(_get())


@app.command()
def text(
    host: str = typer.Argument(..., help="Gopher server hostname"),
    selector: str = typer.Argument(..., help="Resource selector (path)"),
    port: int = typer.Option(
        DEFAULT_PORT,
        "--port",
        "-p",
        help="Server port",
    ),
    timeout: float = typer.Option(
        REQUEST_TIMEOUT,
        "--timeout",
        help="Request timeout in seconds",
    ),
) -> None:
    """Get a text file from a Gopher server.

    This is a convenience command for getting type 0 (text) resources.

    Examples:

        $ mototli text gopher.floodgap.com /gopher/welcome
    """

    async def _get() -> None:
        try:
            async with GopherClient(timeout=timeout) as client:
                content = await client.get_text(
                    host=host,
                    selector=selector,
                    port=port,
                )
                console.print(content)

        except TimeoutError as e:
            error_console.print(f"[red]Timeout:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e
        except ConnectionError as e:
            error_console.print(f"[red]Connection error:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e
        except Exception as e:
            error_console.print(f"[red]Error:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e

    asyncio.run(_get())


@app.command()
def attrs(
    host: str = typer.Argument(..., help="Gopher+ server hostname"),
    selector: str = typer.Argument(..., help="Resource selector (path)"),
    port: int = typer.Option(
        DEFAULT_PORT,
        "--port",
        "-p",
        help="Server port",
    ),
    timeout: float = typer.Option(
        REQUEST_TIMEOUT,
        "--timeout",
        help="Request timeout in seconds",
    ),
) -> None:
    """Get Gopher+ attributes for a resource.

    Examples:

        $ mototli attrs gopher.example.com /about
    """

    async def _get() -> None:
        try:
            async with GopherClient(timeout=timeout) as client:
                attributes = await client.get_attributes(
                    host=host,
                    selector=selector,
                    port=port,
                )

                # Display attributes
                table = Table(title="Gopher+ Attributes", show_header=False)
                table.add_column("Key", style="bold cyan")
                table.add_column("Value")

                if attributes.info:
                    table.add_row("Info", str(attributes.info))
                if attributes.admin:
                    table.add_row("Admin", attributes.admin)
                if attributes.admin_email:
                    table.add_row("Email", attributes.admin_email)
                if attributes.mod_date:
                    table.add_row("Modified", str(attributes.mod_date))
                if attributes.abstract:
                    table.add_row("Abstract", attributes.abstract)
                if attributes.views:
                    views_str = ", ".join(v.mime_type for v in attributes.views)
                    table.add_row("Views", views_str)

                console.print(table)

                # Show raw if no parsed attributes
                if not any(
                    [
                        attributes.info,
                        attributes.admin,
                        attributes.abstract,
                        attributes.views,
                    ]
                ):
                    console.print("\n[dim]Raw attributes:[/]")
                    console.print(attributes.raw)

        except TimeoutError as e:
            error_console.print(f"[red]Timeout:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e
        except ConnectionError as e:
            error_console.print(f"[red]Connection error:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e
        except Exception as e:
            error_console.print(f"[red]Error:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e

    asyncio.run(_get())


@app.command()
def serve(
    root: Path = typer.Argument(
        ".",
        help="Document root directory to serve",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    host: str = typer.Option(
        "localhost",
        "--host",
        "-h",
        help="Host address to bind to",
    ),
    port: int = typer.Option(
        DEFAULT_PORT,
        "--port",
        "-p",
        help="Port to listen on",
    ),
    hostname: str | None = typer.Option(
        None,
        "--hostname",
        help="Public hostname for menu items (defaults to host)",
    ),
    no_directory_listing: bool = typer.Option(
        False,
        "--no-directory-listing",
        help="Disable automatic directory listings",
    ),
    no_gopher_plus: bool = typer.Option(
        False,
        "--no-gopher-plus",
        help="Disable Gopher+ extensions",
    ),
    admin_name: str | None = typer.Option(
        None,
        "--admin-name",
        help="Administrator name for Gopher+ ADMIN block",
    ),
    admin_email: str | None = typer.Option(
        None,
        "--admin-email",
        help="Administrator email for Gopher+ ADMIN block",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to TOML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    init_config: bool = typer.Option(
        False,
        "--init",
        help="Generate an example configuration file and exit",
    ),
) -> None:
    """Start a Gopher server.

    Serves files from the specified document root directory. Supports
    static files, directory listings, CGI scripts, and Gopher+ extensions.

    Examples:

        # Serve current directory on default port (70)
        $ mototli serve

        # Serve a specific directory on a custom port
        $ mototli serve /var/gopher --port 7070

        # Serve with a public hostname
        $ mototli serve /var/gopher --hostname gopher.example.com

        # Serve with Gopher+ admin info
        $ mototli serve /var/gopher --admin-name "John Doe" \\
            --admin-email "john@example.com"

        # Use a configuration file
        $ mototli serve --config gopher.toml

        # Generate an example config file
        $ mototli serve --init > gopher.toml
    """
    from .server.config import ServerConfig
    from .server.server import run_server

    # Generate example config if requested
    if init_config:
        example_config = ServerConfig(
            host=host,
            port=port,
            document_root=root,
            hostname=hostname,
            enable_directory_listing=not no_directory_listing,
            gopher_plus=not no_gopher_plus,
            admin_name=admin_name or "Your Name",
            admin_email=admin_email or "you@example.com",
        )
        # Use print() instead of console.print() to avoid Rich markup interpretation
        print(example_config.to_toml(), end="")
        return

    # Load config from file or create from options
    if config:
        try:
            server_config = ServerConfig.from_toml(config)
            console.print(f"[cyan]Loaded configuration from {config}[/]")
        except Exception as e:
            error_console.print(f"[red]Error loading config:[/] {escape(str(e))}")
            raise typer.Exit(code=1) from e
    else:
        server_config = ServerConfig(
            host=host,
            port=port,
            document_root=root,
            hostname=hostname,
            enable_directory_listing=not no_directory_listing,
            gopher_plus=not no_gopher_plus,
            admin_name=admin_name,
            admin_email=admin_email,
        )

    # Validate configuration
    try:
        server_config.validate()
    except ValueError as e:
        error_console.print(f"[red]Configuration error:[/] {escape(str(e))}")
        raise typer.Exit(code=1) from e

    # Print startup info
    console.print("[bold cyan]Mototli[/] Gopher Server")
    console.print(f"[bold]Document root:[/] {server_config.document_root}")
    console.print(f"[bold]Listening on:[/] {server_config.host}:{server_config.port}")
    pub_host = server_config.public_hostname
    pub_port = server_config.public_port
    console.print(f"[bold]Public hostname:[/] {pub_host}:{pub_port}")
    if server_config.gopher_plus:
        console.print("[bold]Gopher+:[/] enabled")
    console.print()
    console.print("[dim]Press Ctrl+C to stop[/]")
    console.print()

    # Run the server
    try:
        asyncio.run(run_server(server_config))
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/]")
    except Exception as e:
        error_console.print(f"[red]Server error:[/] {escape(str(e))}")
        raise typer.Exit(code=1) from e


@app.command()
def version() -> None:
    """Show version information."""
    try:
        ver = get_version("mototli")
    except Exception:
        ver = "0.1.0"

    console.print("[bold cyan]Mototli[/] Gopher Protocol Client and Server")
    console.print(f"[bold]Version:[/] {ver}")
    console.print("[bold]Protocol:[/] Gopher (RFC 1436) with Gopher+ (RFC 4266)")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
