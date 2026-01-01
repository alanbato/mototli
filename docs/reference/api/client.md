# Client API

API reference for the Mototli Gopher client.

## GopherClient

::: mototli.client.GopherClient
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get
        - get_text
        - get_binary
        - get_attributes
        - get_with_view

## Usage Examples

### Basic Usage

```python
import asyncio
from mototli.client import GopherClient

async def main():
    async with GopherClient(timeout=30.0) as client:
        response = await client.get("gopher.floodgap.com", "/")
        for item in response.items:
            print(f"[{item.item_type.value}] {item.display_text}")

asyncio.run(main())
```

### Fetching Text

```python
async with GopherClient() as client:
    response = await client.get_text("gopher.floodgap.com", "/gopher/welcome")
    print(response.content.decode())
```

### Fetching Binary

```python
async with GopherClient() as client:
    response = await client.get_binary("gopher.floodgap.com", "/file.zip")
    with open("file.zip", "wb") as f:
        f.write(response.content)
```

### Gopher+ Attributes

```python
async with GopherClient() as client:
    attrs = await client.get_attributes("gopher.floodgap.com", "/gopher")
    print(f"Admin: {attrs.admin.name}")
    print(f"Views: {[v.content_type for v in attrs.views]}")
```

### Search Queries

```python
async with GopherClient() as client:
    response = await client.get(
        "gopher.floodgap.com",
        "/v2/vs",
        search_query="python"
    )
    for item in response.items:
        print(item.display_text)
```

## Error Handling

```python
try:
    async with GopherClient(timeout=10.0) as client:
        response = await client.get("example.com", "/")
except TimeoutError:
    print("Connection timed out")
except ConnectionRefusedError:
    print("Connection refused")
except OSError as e:
    print(f"Network error: {e}")
```

## See Also

- [:octicons-arrow-right-24: Building a Client](../../tutorials/building-a-client.md) - Tutorial
- [:octicons-arrow-right-24: Fetch Resources](../../how-to/fetch-resources.md) - How-to guide
- [:octicons-arrow-right-24: Protocol API](protocol.md) - Response types
