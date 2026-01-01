# Mototli

[![CI](https://github.com/alanbato/mototli/actions/workflows/ci.yml/badge.svg)](https://github.com/alanbato/mototli/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/mototli.svg)](https://pypi.org/project/mototli/)
[![codecov](https://codecov.io/gh/alanbato/mototli/branch/main/graph/badge.svg)](https://codecov.io/gh/alanbato/mototli)
[![Python versions](https://img.shields.io/pypi/pyversions/mototli.svg)](https://pypi.org/project/mototli/)
[![License](https://img.shields.io/github/license/alanbato/mototli.svg)](https://github.com/alanbato/mototli/blob/main/LICENSE)
[![Documentation](https://readthedocs.org/projects/mototli/badge/?version=latest)](https://mototli.readthedocs.io)

**Modern Gopher protocol server and client implementation using asyncio.**

Mototli brings the classic [Gopher protocol](https://en.wikipedia.org/wiki/Gopher_(protocol)) (RFC 1436) into modern Python with full [Gopher+](https://en.wikipedia.org/wiki/Gopher%2B) extensions (RFC 4266), async/await support, and a developer-friendly API.

Part of the small internet protocol family alongside [Nauyaca](https://github.com/alanbato/nauyaca) (Gemini) and Mapilli.

## Features

- **Async Client** - Browse gopherspace with an elegant async API
- **Full Server** - Host your own gopherhole with static files, CGI, and directory listings
- **Gopher+ Support** - Complete RFC 4266 implementation with attributes and views
- **CLI Tools** - Rich command-line interface for browsing and serving
- **TOML Config** - Flexible server configuration
- **Type Safe** - Full type hints with strict mypy

## Installation

```bash
# Using uv (recommended)
uv add mototli

# Using pip
pip install mototli
```

## Quick Start

### Browse Gopherspace

```bash
# Fetch a directory listing
mototli get gopher.floodgap.com

# Fetch a text file
mototli text gopher.floodgap.com /gopher/welcome

# Get Gopher+ attributes
mototli attrs gopher.floodgap.com /gopher
```

### Serve a Gopherhole

```bash
# Serve current directory
mototli serve --port 7070

# With configuration
mototli serve --config server.toml
```

### Python Client

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

### Python Server

```python
import asyncio
from mototli.server import run_server

asyncio.run(run_server(document_root="./gopherhole", port=7070))
```

## Documentation

Full documentation is available at [mototli.readthedocs.io](https://mototli.readthedocs.io):

- [Installation Guide](https://mototli.readthedocs.io/installation/)
- [Quick Start](https://mototli.readthedocs.io/quickstart/)
- [Tutorials](https://mototli.readthedocs.io/tutorials/)
- [API Reference](https://mototli.readthedocs.io/reference/api/)

## Development

```bash
# Clone and install
git clone https://github.com/alanbato/mototli.git
cd mototli
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/

# Build docs locally
uv run mkdocs serve
```

## License

MIT License - see [LICENSE](LICENSE) for details.
