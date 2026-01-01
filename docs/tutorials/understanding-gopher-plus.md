# Understanding Gopher+

Gopher+ (RFC 4266) extends the classic Gopher protocol with metadata, alternate views, and enhanced capabilities. In this tutorial, you'll learn how to:

- Query item attributes with the `$` modifier
- Request specific views with the `+` modifier
- Access admin information and abstracts
- Enable Gopher+ on your server

**Difficulty**: Intermediate
**Time**: ~25 minutes
**Prerequisites**: Complete [Your First Gopherhole](your-first-gopherhole.md) or [Building a Client](building-a-client.md)

---

## What is Gopher+?

Gopher+ adds several capabilities to the original protocol:

| Feature | Description |
|---------|-------------|
| **Attributes** | Metadata about items (size, MIME type, language) |
| **Views** | Alternate representations of content |
| **Admin Info** | Server administrator contact information |
| **Abstracts** | Short descriptions of items |

---

## Step 1: Query attributes with the CLI

The Mototli CLI can query Gopher+ attributes:

```bash
mototli attrs gopher.floodgap.com /gopher
```

Example output:

```
+INFO: 1Welcome to Floodgap	/gopher	gopher.floodgap.com	70	+
+ADMIN:
  Admin: Cameron Kaiser <ckaiser@floodgap.com>
  Mod-Date: 2024-01-15
+VIEWS:
  text/plain: <50k>
  application/gopher-menu: <2k>
+ABSTRACT:
  The Floodgap gopher server, online since 1999.
```

---

## Step 2: Query attributes programmatically

Use `get_attributes()` to fetch Gopher+ metadata:

```python
import asyncio
from mototli.client import GopherClient


async def main():
    async with GopherClient() as client:
        # Fetch attributes for an item
        attrs = await client.get_attributes(
            host="gopher.floodgap.com",
            selector="/gopher"
        )

        # Access parsed attributes
        if attrs.info:
            print(f"Item Type: {attrs.info.item_type}")
            print(f"Display: {attrs.info.display_text}")

        if attrs.admin:
            print(f"Admin: {attrs.admin.name}")
            print(f"Email: {attrs.admin.email}")

        if attrs.views:
            print("Available views:")
            for view in attrs.views:
                print(f"  - {view.content_type}: {view.size}")

        if attrs.abstract:
            print(f"Abstract: {attrs.abstract}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 3: Understand request modifiers

Gopher+ uses special characters appended to selectors:

| Modifier | Meaning | Example |
|----------|---------|---------|
| `$` | Request attributes only | `/file$` |
| `+` | Request specific view | `/file+text/plain` |
| `!` | Request with attributes | `/file!` |

The `$` modifier fetches metadata without downloading content:

```python
# This fetches only metadata, not the file content
attrs = await client.get_attributes(host, "/largefile.zip")
print(f"File size: {attrs.info.size} bytes")
```

---

## Step 4: Request a specific view

Some items have multiple representations. Use `get_with_view()`:

```python
import asyncio
from mototli.client import GopherClient


async def main():
    async with GopherClient() as client:
        # First, check available views
        attrs = await client.get_attributes(
            "gopher.example.com",
            "/document"
        )

        print("Available views:")
        for view in attrs.views:
            print(f"  {view.content_type}")

        # Request a specific view
        response = await client.get_with_view(
            host="gopher.example.com",
            selector="/document",
            view_type="text/plain"
        )

        print(response.content.decode())


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 5: Enable Gopher+ on your server

Mototli's server has Gopher+ enabled by default. Start a server:

```bash
mototli serve ./my-gopherhole --port 7070
```

Verify Gopher+ is working:

```bash
mototli attrs localhost:7070 /
```

You should see attribute information including admin details.

---

## Step 6: Configure server Gopher+ settings

Use a TOML configuration file for advanced settings:

```toml
# server.toml
[server]
host = "0.0.0.0"
port = 7070
hostname = "my-gopherhole.example.com"
document_root = "./content"

[gopher_plus]
enabled = true
admin_name = "Your Name"
admin_email = "you@example.com"
```

Start with your config:

```bash
mototli serve --config server.toml
```

Now your attributes will include your admin information:

```bash
mototli attrs localhost:7070 /
```

```
+ADMIN:
  Admin: Your Name <you@example.com>
```

---

## Step 7: Add abstracts to your content

Abstracts provide short descriptions. Create a `.abstract` file alongside your content:

```bash
cd my-gopherhole

# Create a text file
echo "This is my main document." > document.txt

# Create its abstract
echo "A brief introduction to my gopherhole." > document.txt.abstract
```

Query the attributes:

```bash
mototli attrs localhost:7070 /document.txt
```

```
+ABSTRACT:
  A brief introduction to my gopherhole.
```

---

## Step 8: Detect Gopher+ support

Not all servers support Gopher+. Check before using advanced features:

```python
import asyncio
from mototli.client import GopherClient


async def check_gopher_plus(host: str, selector: str = "/"):
    """Check if a server supports Gopher+."""
    async with GopherClient(timeout=10.0) as client:
        try:
            attrs = await client.get_attributes(host, selector)
            # If we got attributes, Gopher+ is supported
            return attrs is not None
        except Exception:
            return False


async def main():
    servers = [
        "gopher.floodgap.com",
        "localhost:7070",
    ]

    for server in servers:
        parts = server.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 70

        supported = await check_gopher_plus(host)
        status = "Yes" if supported else "No"
        print(f"{server}: Gopher+ supported: {status}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Attribute Block Reference

Gopher+ responses contain several attribute blocks:

### +INFO

Basic item information:

```
+INFO: 0document.txt	/document.txt	localhost	7070	+
```

Fields: item_type, display_text, selector, host, port, gopher_plus_flag

### +ADMIN

Server administrator information:

```
+ADMIN:
 Admin: Name <email@example.com>
 Mod-Date: 2024-01-15
```

### +VIEWS

Available content representations:

```
+VIEWS:
 text/plain: <15k>
 text/html: <25k>
```

### +ABSTRACT

Short description:

```
+ABSTRACT:
 A brief summary of this item.
```

---

## Summary

You've learned how to:

- [x] Query Gopher+ attributes with `$` modifier
- [x] Use `get_attributes()` for programmatic access
- [x] Request specific views with `+` modifier
- [x] Enable and configure Gopher+ on your server
- [x] Add abstracts to your content
- [x] Detect Gopher+ support on servers

---

## Common Issues

### "No attributes returned"

The server may not support Gopher+. Try a known Gopher+ server:

```bash
mototli attrs gopher.floodgap.com /gopher
```

### "Connection reset"

Some servers disconnect when receiving Gopher+ requests. This indicates no Gopher+ support.

### Views not working

Not all items have alternate views. Check available views first:

```python
attrs = await client.get_attributes(host, selector)
print(attrs.views)  # May be empty
```

---

## Next Steps

- [:octicons-arrow-right-24: Gopher+ Explanation](../explanation/gopher-plus.md) - Deep dive into RFC 4266
- [:octicons-arrow-right-24: Configure Server](../how-to/configure-server.md) - Advanced configuration
- [:octicons-arrow-right-24: Protocol API](../reference/api/protocol.md) - Attribute classes reference
