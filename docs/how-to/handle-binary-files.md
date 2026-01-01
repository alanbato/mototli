# Handle Binary Files

This guide shows how to serve and fetch binary content like images and archives.

## Prerequisites

- Mototli [installed](../installation.md)
- Basic familiarity with the client or server

## Serving binary files

Binary files are served automatically based on file extension.

### MIME type detection

Mototli detects file types and maps them to Gopher item types:

| Extension | MIME Type | Item Type |
|-----------|-----------|-----------|
| `.gif` | image/gif | `g` (GIF) |
| `.png`, `.jpg` | image/* | `I` (Image) |
| `.tar`, `.zip` | application/* | `9` (Binary) |
| `.mp3`, `.wav` | audio/* | `s` (Sound) |
| `.pdf` | application/pdf | `d` (Document) |

### Add binary files to your gopherhole

```bash
cp ~/photos/image.png my-gopherhole/
cp ~/archives/data.tar.gz my-gopherhole/
```

Auto-generated listings will use the correct item types.

### Explicit gophermap entries

For manual control, specify the type in your gophermap:

```
gLogo	/logo.gif	localhost	7070
IPhoto Gallery	/photo.png	localhost	7070
9Download Archive	/data.tar.gz	localhost	7070
sBackground Music	/ambient.mp3	localhost	7070
```

## Configure file size limits

Prevent serving extremely large files:

```toml
[handlers]
max_file_size = 104857600  # 100 MiB
```

Files exceeding this limit return an error.

## Fetching binary files with CLI

Use the `get` command with `--type 9`:

```bash
mototli get localhost:7070 /data.tar.gz --type 9 > data.tar.gz
```

Or use `--raw` to output binary content:

```bash
mototli get localhost:7070 /data.tar.gz --raw > data.tar.gz
```

## Fetching binary files with Python

Use `get_binary()` for binary content:

```python
import asyncio
from pathlib import Path
from mototli.client import GopherClient


async def download_file(host: str, selector: str, output: str):
    async with GopherClient() as client:
        response = await client.get_binary(host, selector)

        output_path = Path(output)
        output_path.write_bytes(response.content)

        print(f"Downloaded {len(response.content)} bytes to {output}")


asyncio.run(download_file("localhost:7070", "/data.tar.gz", "data.tar.gz"))
```

## Download multiple files

```python
import asyncio
from pathlib import Path
from mototli.client import GopherClient


async def download_files(host: str, files: list[tuple[str, str]]):
    """Download multiple files from a gopher server.

    Args:
        host: Server hostname
        files: List of (selector, output_filename) tuples
    """
    async with GopherClient() as client:
        for selector, output in files:
            try:
                response = await client.get_binary(host, selector)
                Path(output).write_bytes(response.content)
                print(f"Downloaded: {output} ({len(response.content)} bytes)")
            except Exception as e:
                print(f"Failed: {selector} - {e}")


files = [
    ("/images/logo.gif", "logo.gif"),
    ("/images/banner.png", "banner.png"),
    ("/archives/data.tar.gz", "data.tar.gz"),
]

asyncio.run(download_files("localhost:7070", files))
```

## Check file size before downloading

With Gopher+, you can check size without downloading:

```python
import asyncio
from mototli.client import GopherClient


async def check_and_download(host: str, selector: str, max_size: int = 10_000_000):
    """Download only if file is under max_size bytes."""
    async with GopherClient() as client:
        # Get attributes first
        attrs = await client.get_attributes(host, selector)

        if attrs.info and attrs.info.size:
            size = attrs.info.size
            if size > max_size:
                print(f"File too large: {size} bytes (max: {max_size})")
                return None

            print(f"Downloading {size} bytes...")

        response = await client.get_binary(host, selector)
        return response.content


asyncio.run(check_and_download("localhost:7070", "/large-file.zip"))
```

## Detect item type from response

```python
from mototli.utils import get_item_type, get_mime_type
from pathlib import Path

# From file extension
path = Path("image.png")
item_type = get_item_type(path)
mime_type = get_mime_type(path)

print(f"Item type: {item_type}")  # ItemType.IMAGE
print(f"MIME type: {mime_type}")  # image/png
```

## Progress indication

For large downloads, track progress:

```python
import asyncio
from mototli.client import GopherClient


async def download_with_progress(host: str, selector: str, output: str):
    async with GopherClient() as client:
        # Get size first (Gopher+ only)
        try:
            attrs = await client.get_attributes(host, selector)
            total_size = attrs.info.size if attrs.info else None
        except Exception:
            total_size = None

        # Download
        response = await client.get_binary(host, selector)

        # Save
        with open(output, "wb") as f:
            f.write(response.content)

        if total_size:
            print(f"Downloaded {len(response.content)}/{total_size} bytes")
        else:
            print(f"Downloaded {len(response.content)} bytes")


asyncio.run(download_with_progress("localhost:7070", "/file.zip", "file.zip"))
```

## Troubleshooting

### "File corrupted"

Binary files must be fetched with binary mode:

```python
# Correct
response = await client.get_binary(host, selector)

# Wrong - decodes as text, corrupts binary data
response = await client.get_text(host, selector)
```

### "File too large"

Increase the server's file size limit:

```toml
[handlers]
max_file_size = 524288000  # 500 MiB
```

### "Unknown item type"

Add the extension to MIME mapping or use explicit item type in gophermap.

## See also

- [:octicons-arrow-right-24: Item Types Reference](../reference/item-types.md) - Complete type list
- [:octicons-arrow-right-24: Fetch Resources](fetch-resources.md) - More fetching patterns
- [:octicons-arrow-right-24: Protocol API](../reference/api/protocol.md) - ItemType enum
