# Fetch Resources

This guide covers advanced patterns for fetching gopher content with the Python client.

## Prerequisites

- Mototli [installed](../installation.md)
- Completed [Building a Client](../tutorials/building-a-client.md) tutorial

## Basic fetching

The `GopherClient` provides several fetch methods:

```python
from mototli.client import GopherClient

async with GopherClient() as client:
    # Fetch directory listing
    response = await client.get(host, selector)

    # Fetch text file
    response = await client.get_text(host, selector)

    # Fetch binary file
    response = await client.get_binary(host, selector)

    # Fetch Gopher+ attributes
    attrs = await client.get_attributes(host, selector)

    # Fetch with specific view
    response = await client.get_with_view(host, selector, "text/plain")
```

## Configure timeout

Set timeout at client creation:

```python
# Short timeout for quick checks
client = GopherClient(timeout=5.0)

# Long timeout for slow servers
client = GopherClient(timeout=120.0)
```

## Handle search queries

Type 7 (search) items accept a query:

```python
async with GopherClient() as client:
    # Fetch search results
    response = await client.get(
        host="gopher.floodgap.com",
        selector="/v2/vs",
        search_query="python programming"
    )

    for item in response.items:
        print(f"[{item.item_type.value}] {item.display_text}")
```

## Specify item type

Force a specific item type:

```python
from mototli.protocol import ItemType

async with GopherClient() as client:
    response = await client.get(
        host="example.com",
        selector="/file",
        item_type=ItemType.TEXT  # Treat as text
    )
```

## Recursive directory crawling

Crawl a gopherhole recursively:

```python
import asyncio
from mototli.client import GopherClient
from mototli.protocol import ItemType


async def crawl(client: GopherClient, host: str, selector: str = "/",
                visited: set | None = None, depth: int = 0, max_depth: int = 3):
    """Recursively crawl a gopherhole."""
    if visited is None:
        visited = set()

    key = (host, selector)
    if key in visited or depth > max_depth:
        return

    visited.add(key)
    indent = "  " * depth

    try:
        response = await client.get(host, selector)
        print(f"{indent}[DIR] {selector}")

        for item in response.items:
            if item.item_type == ItemType.DIRECTORY:
                # Recursively crawl subdirectories
                await crawl(client, item.host, item.selector,
                           visited, depth + 1, max_depth)
            elif item.item_type == ItemType.TEXT:
                print(f"{indent}  [TXT] {item.display_text}")
            elif item.item_type.is_binary:
                print(f"{indent}  [BIN] {item.display_text}")

    except Exception as e:
        print(f"{indent}[ERR] {selector}: {e}")


async def main():
    async with GopherClient(timeout=10.0) as client:
        await crawl(client, "gopher.floodgap.com", "/gopher")


asyncio.run(main())
```

## Parallel fetching

Fetch multiple resources concurrently:

```python
import asyncio
from mototli.client import GopherClient


async def fetch_all(host: str, selectors: list[str]):
    """Fetch multiple selectors in parallel."""
    async with GopherClient() as client:
        tasks = [client.get_text(host, sel) for sel in selectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for selector, result in zip(selectors, results):
            if isinstance(result, Exception):
                print(f"Error fetching {selector}: {result}")
            else:
                print(f"{selector}: {len(result.content)} bytes")

        return results


selectors = ["/file1.txt", "/file2.txt", "/file3.txt"]
asyncio.run(fetch_all("localhost:7070", selectors))
```

## Retry with backoff

Implement retry logic for unreliable connections:

```python
import asyncio
from mototli.client import GopherClient


async def fetch_with_retry(host: str, selector: str,
                          max_retries: int = 3, base_delay: float = 1.0):
    """Fetch with exponential backoff retry."""
    last_error = None

    for attempt in range(max_retries):
        try:
            async with GopherClient(timeout=10.0) as client:
                return await client.get(host, selector)

        except (TimeoutError, ConnectionError) as e:
            last_error = e
            delay = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
            await asyncio.sleep(delay)

    raise last_error


asyncio.run(fetch_with_retry("slow-server.example", "/"))
```

## Cache responses

Simple in-memory caching:

```python
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from mototli.client import GopherClient


@dataclass
class CacheEntry:
    response: object
    expires: datetime


class CachingClient:
    def __init__(self, ttl_seconds: int = 300):
        self.client = GopherClient()
        self.cache: dict[tuple, CacheEntry] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    async def get(self, host: str, selector: str):
        key = (host, selector)
        now = datetime.now()

        # Check cache
        if key in self.cache and self.cache[key].expires > now:
            return self.cache[key].response

        # Fetch and cache
        async with self.client:
            response = await self.client.get(host, selector)

        self.cache[key] = CacheEntry(
            response=response,
            expires=now + self.ttl
        )

        return response


async def main():
    client = CachingClient(ttl_seconds=60)

    # First fetch - hits server
    await client.get("gopher.floodgap.com", "/")

    # Second fetch - from cache
    await client.get("gopher.floodgap.com", "/")


asyncio.run(main())
```

## Stream large files

For very large files, process in chunks:

```python
import asyncio
from mototli.client import GopherClient


async def download_large_file(host: str, selector: str, output: str):
    """Download a large file."""
    # Note: Gopher doesn't support streaming, so we get the full response
    # For very large files, you may need to increase timeout
    async with GopherClient(timeout=300.0) as client:
        response = await client.get_binary(host, selector)

        # Write in chunks to avoid memory issues
        chunk_size = 8192
        with open(output, "wb") as f:
            for i in range(0, len(response.content), chunk_size):
                chunk = response.content[i:i + chunk_size]
                f.write(chunk)

        print(f"Downloaded {len(response.content)} bytes")


asyncio.run(download_large_file("example.com", "/large-file.zip", "output.zip"))
```

## Error handling patterns

Comprehensive error handling:

```python
import asyncio
from mototli.client import GopherClient


async def safe_fetch(host: str, selector: str):
    """Fetch with comprehensive error handling."""
    try:
        async with GopherClient(timeout=30.0) as client:
            return await client.get(host, selector)

    except TimeoutError:
        print(f"Timeout connecting to {host}")
        return None

    except ConnectionRefusedError:
        print(f"Connection refused by {host}")
        return None

    except ConnectionResetError:
        print(f"Connection reset by {host}")
        return None

    except OSError as e:
        print(f"Network error: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        return None
```

## See also

- [:octicons-arrow-right-24: Client API](../reference/api/client.md) - Complete API reference
- [:octicons-arrow-right-24: Handle Binary Files](handle-binary-files.md) - Binary content
- [:octicons-arrow-right-24: Building a Client](../tutorials/building-a-client.md) - Client tutorial
