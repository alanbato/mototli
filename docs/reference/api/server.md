# Server API

API reference for the Mototli Gopher server.

## GopherServer

::: mototli.server.GopherServer
    options:
      show_root_heading: true
      show_source: true

## ServerConfig

::: mototli.server.ServerConfig
    options:
      show_root_heading: true
      show_source: true

## Router

::: mototli.server.Router
    options:
      show_root_heading: true
      show_source: true

## RouteType

::: mototli.server.RouteType
    options:
      show_root_heading: true

## Convenience Functions

### run_server

::: mototli.server.run_server
    options:
      show_root_heading: true
      show_source: true

### start_server

::: mototli.server.start_server
    options:
      show_root_heading: true
      show_source: true

## Handlers

### RequestHandler

::: mototli.server.RequestHandler
    options:
      show_root_heading: true
      show_source: true

### StaticFileHandler

::: mototli.server.StaticFileHandler
    options:
      show_root_heading: true
      show_source: true

### CGIHandler

::: mototli.server.CGIHandler
    options:
      show_root_heading: true
      show_source: true

### ErrorHandler

::: mototli.server.ErrorHandler
    options:
      show_root_heading: true
      show_source: true

## Usage Examples

### Quick Start

```python
import asyncio
from mototli.server import run_server

# Serve current directory on port 7070
asyncio.run(run_server(document_root=".", port=7070))
```

### With Configuration

```python
import asyncio
from mototli.server import GopherServer, ServerConfig
from pathlib import Path

config = ServerConfig(
    host="0.0.0.0",
    port=7070,
    hostname="gopher.example.com",
    document_root=Path("/var/gopher"),
    gopher_plus=True,
    admin_name="Admin",
    admin_email="admin@example.com"
)

async def main():
    server = GopherServer(config)
    await server.start()
    try:
        await asyncio.Event().wait()  # Run forever
    finally:
        await server.stop()

asyncio.run(main())
```

### From TOML File

```python
import asyncio
from mototli.server import GopherServer, ServerConfig

config = ServerConfig.from_toml("server.toml")

async def main():
    server = GopherServer(config)
    await server.start()
    await asyncio.Event().wait()

asyncio.run(main())
```

### Custom Routing

```python
from mototli.server import Router, RouteType

router = Router()

# Exact match
router.add_route("/about", about_handler, RouteType.EXACT)

# Prefix match
router.add_route("/files/", file_handler, RouteType.PREFIX)
```

### Custom Handler

```python
from mototli.server import RequestHandler
from mototli.protocol import GopherRequest, GopherResponse

class CustomHandler(RequestHandler):
    async def handle(self, request: GopherRequest) -> GopherResponse:
        # Generate custom response
        content = f"You requested: {request.selector}"
        return GopherResponse(content=content.encode())
```

## See Also

- [:octicons-arrow-right-24: Your First Gopherhole](../../tutorials/your-first-gopherhole.md) - Tutorial
- [:octicons-arrow-right-24: Configure Server](../../how-to/configure-server.md) - Configuration guide
- [:octicons-arrow-right-24: Configuration Reference](../configuration.md) - TOML options
