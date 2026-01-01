# Mototli

**Modern Gopher protocol server and client implementation using asyncio**

Mototli is a Python library that brings the classic Gopher protocol (RFC 1436) into the modern era with full Gopher+ extensions (RFC 4266), async/await support, and a developer-friendly API.

<div class="grid cards" markdown>

-   :material-server: **Serve Content**

    ---

    Host your own gopherhole with a full-featured async server supporting CGI, directory listings, and Gopher+ attributes.

    [:octicons-arrow-right-24: Quick Start](quickstart.md)

-   :material-download: **Fetch Resources**

    ---

    Browse gopherspace programmatically with an elegant async client that handles directories, text, and binary content.

    [:octicons-arrow-right-24: Client Tutorial](tutorials/building-a-client.md)

-   :material-console: **CLI Tools**

    ---

    Explore gopher servers from the command line with rich output formatting and Gopher+ support.

    [:octicons-arrow-right-24: CLI Reference](reference/cli.md)

-   :material-plus-circle: **Gopher+ Ready**

    ---

    Full support for Gopher+ extensions including attribute queries, alternate views, and admin information.

    [:octicons-arrow-right-24: Gopher+ Guide](tutorials/understanding-gopher-plus.md)

</div>

## Quick Example

=== "Client"

    ```python
    import asyncio
    from mototli.client import GopherClient

    async def main():
        async with GopherClient() as client:
            response = await client.get("gopher.floodgap.com", "/")
            for item in response.items:
                print(f"[{item.item_type.value}] {item.display_text}")

    asyncio.run(main())
    ```

=== "Server"

    ```python
    import asyncio
    from mototli.server import run_server

    asyncio.run(run_server(document_root="./gopherhole"))
    ```

=== "CLI"

    ```bash
    # Browse a gopher server
    mototli get gopher.floodgap.com

    # Serve a local directory
    mototli serve ./my-gopherhole --port 7070
    ```

## Installation

```bash
# Using uv (recommended)
uv add mototli

# Using pip
pip install mototli
```

[:octicons-arrow-right-24: Full installation guide](installation.md)

## Key Features

| Feature | Description |
|---------|-------------|
| **Async/Await** | Built on asyncio for high-performance networking |
| **Gopher+ Support** | Full RFC 4266 implementation with attributes and views |
| **CLI Included** | Rich command-line interface for browsing and serving |
| **TOML Config** | Flexible server configuration via TOML files |
| **CGI Support** | Execute CGI scripts for dynamic content |
| **Type Safe** | Full type hints and mypy strict mode |

## Project Status

Mototli is in active development:

- [x] Protocol definitions (RFC 1436)
- [x] Gopher+ extensions (RFC 4266)
- [x] Async client with directory/text/binary support
- [x] Full-featured async server
- [x] CGI script execution
- [x] Command-line interface
- [x] TOML configuration
- [ ] TLS support (Gopher/S)
- [ ] Caching layer

## Next Steps

<div class="grid cards" markdown>

-   :material-rocket-launch: **Get Started**

    [:octicons-arrow-right-24: Quick Start Guide](quickstart.md)

-   :material-school: **Learn**

    [:octicons-arrow-right-24: Tutorials](tutorials/index.md)

-   :material-book-open-variant: **Reference**

    [:octicons-arrow-right-24: API Documentation](reference/api/index.md)

</div>
