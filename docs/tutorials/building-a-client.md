# Building a Client

In this tutorial, you'll build a Python client to browse gopherspace programmatically. You'll learn how to:

- Connect to gopher servers asynchronously
- Parse and display directory listings
- Fetch text and binary content
- Handle errors gracefully

**Difficulty**: Intermediate
**Time**: ~20 minutes
**Prerequisites**: [Mototli installed](../installation.md), basic Python async/await knowledge

---

## Step 1: Create your project

Create a new directory for your client:

```bash
mkdir gopher-client
cd gopher-client
```

Create a `client.py` file:

```python
import asyncio
from mototli.client import GopherClient


async def main():
    print("Gopher Client Ready!")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it to verify your setup:

```bash
python client.py
```

---

## Step 2: Connect and fetch a directory

The `GopherClient` uses a context manager pattern for automatic connection handling:

```python
import asyncio
from mototli.client import GopherClient


async def main():
    # Create a client with a 30-second timeout
    async with GopherClient(timeout=30.0) as client:
        # Fetch the root directory
        response = await client.get("gopher.floodgap.com", "/")

        print(f"Fetched {len(response.items)} items")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python client.py
```

You should see something like:

```
Fetched 42 items
```

---

## Step 3: Display directory items

Each item in a directory listing has properties you can access:

```python
import asyncio
from mototli.client import GopherClient


async def main():
    async with GopherClient(timeout=30.0) as client:
        response = await client.get("gopher.floodgap.com", "/")

        for item in response.items:
            # Skip informational items for cleaner output
            if item.item_type.is_informational:
                continue

            # Show item type and display text
            type_char = item.item_type.value
            print(f"[{type_char}] {item.display_text}")
            print(f"    Selector: {item.selector}")
            print(f"    Host: {item.host}:{item.port}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
```

Output:

```
[1] Welcome to Floodgap Systems
    Selector: /gopher
    Host: gopher.floodgap.com:70

[0] The Overbite Project
    Selector: /overbite
    Host: gopher.floodgap.com:70
...
```

---

## Step 4: Fetch text content

Use `get_text()` for text files (item type 0):

```python
import asyncio
from mototli.client import GopherClient


async def fetch_text_file():
    async with GopherClient() as client:
        # Fetch a specific text file
        response = await client.get_text(
            host="gopher.floodgap.com",
            selector="/gopher/wbgopher"
        )

        # Content is bytes, decode to string
        text = response.content.decode("utf-8", errors="replace")
        print(text)


if __name__ == "__main__":
    asyncio.run(fetch_text_file())
```

---

## Step 5: Fetch binary content

Use `get_binary()` for binary files (images, archives, etc.):

```python
import asyncio
from pathlib import Path
from mototli.client import GopherClient


async def download_file():
    async with GopherClient() as client:
        # Fetch a binary file
        response = await client.get_binary(
            host="gopher.floodgap.com",
            selector="/gopher/welcome.gif"
        )

        # Save to disk
        output_path = Path("welcome.gif")
        output_path.write_bytes(response.content)

        print(f"Downloaded {len(response.content)} bytes to {output_path}")


if __name__ == "__main__":
    asyncio.run(download_file())
```

---

## Step 6: Build an interactive browser

Let's combine everything into a simple interactive browser:

```python
import asyncio
from mototli.client import GopherClient
from mototli.protocol import ItemType


class GopherBrowser:
    def __init__(self):
        self.client = GopherClient(timeout=30.0)
        self.history: list[tuple[str, str, int]] = []

    async def browse(self, host: str, selector: str = "/", port: int = 70):
        """Fetch and display a directory."""
        async with self.client:
            response = await self.client.get(host, selector, port=port)

        self.history.append((host, selector, port))

        # Collect non-info items for numbered selection
        items = []
        for item in response.items:
            if item.item_type.is_informational:
                print(f"     {item.display_text}")
            else:
                items.append(item)
                print(f"[{len(items):2}] [{item.item_type.value}] {item.display_text}")

        return items

    async def view_text(self, host: str, selector: str, port: int = 70):
        """Fetch and display a text file."""
        async with self.client:
            response = await self.client.get_text(host, selector, port=port)

        print("\n" + "=" * 60)
        print(response.content.decode("utf-8", errors="replace"))
        print("=" * 60 + "\n")


async def main():
    browser = GopherBrowser()

    # Start at floodgap
    host = "gopher.floodgap.com"
    selector = "/"
    port = 70

    while True:
        print(f"\n=== {host}{selector} ===\n")
        items = await browser.browse(host, selector, port)

        # Get user input
        print("\nEnter number to follow link, 'q' to quit, 'b' to go back:")
        choice = input("> ").strip().lower()

        if choice == "q":
            break
        elif choice == "b":
            if len(browser.history) > 1:
                browser.history.pop()  # Remove current
                host, selector, port = browser.history.pop()  # Get previous
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                item = items[idx]
                if item.item_type == ItemType.DIRECTORY:
                    host = item.host
                    selector = item.selector
                    port = item.port
                elif item.item_type == ItemType.TEXT:
                    await browser.view_text(item.host, item.selector, item.port)
                else:
                    print(f"Unsupported type: {item.item_type}")
        except ValueError:
            print("Invalid input")


if __name__ == "__main__":
    asyncio.run(main())
```

Run your browser:

```bash
python client.py
```

---

## Step 7: Add error handling

Real-world clients need robust error handling:

```python
import asyncio
from mototli.client import GopherClient


async def safe_fetch(host: str, selector: str = "/"):
    """Fetch with proper error handling."""
    try:
        async with GopherClient(timeout=10.0) as client:
            response = await client.get(host, selector)
            return response

    except TimeoutError:
        print(f"Error: Connection to {host} timed out")
        return None

    except ConnectionRefusedError:
        print(f"Error: {host} refused the connection")
        return None

    except OSError as e:
        print(f"Error: Network error - {e}")
        return None


async def main():
    # Try a working server
    response = await safe_fetch("gopher.floodgap.com")
    if response:
        print(f"Success! Got {len(response.items)} items")

    # Try a non-existent server
    response = await safe_fetch("nonexistent.example.com")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Summary

You've learned how to:

- [x] Create a `GopherClient` with timeout configuration
- [x] Fetch directory listings with `get()`
- [x] Access item properties (type, selector, host, port)
- [x] Fetch text content with `get_text()`
- [x] Download binary files with `get_binary()`
- [x] Build an interactive browser
- [x] Handle network errors gracefully

---

## Common Issues

### "Connection timed out"

The server may be slow or unreachable. Increase the timeout:

```python
GopherClient(timeout=60.0)
```

### Encoding errors

Gopher predates Unicode. Use error handling when decoding:

```python
text = response.content.decode("utf-8", errors="replace")
```

### "Connection refused"

The server isn't running or the port is wrong. Check:

```python
await client.get("localhost", "/", port=7070)  # Not 70
```

---

## Next Steps

- [:octicons-arrow-right-24: Understanding Gopher+](understanding-gopher-plus.md) - Learn Gopher+ extensions
- [:octicons-arrow-right-24: Fetch Resources](../how-to/fetch-resources.md) - Advanced fetching patterns
- [:octicons-arrow-right-24: Client API](../reference/api/client.md) - Full API reference
