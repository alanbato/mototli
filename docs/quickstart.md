# Quick Start

Get up and running with Mototli in minutes. This guide covers three common scenarios.

## Scenario 1: Browse Gopherspace

Use the CLI to explore existing gopher servers.

### Step 1: Fetch a directory listing

```bash
mototli get gopher.floodgap.com
```

You'll see a formatted directory listing:

```
[DIR]  /gopher       Welcome to Floodgap
[TXT]  /gopher/glog  The Gopher Gazette
[DIR]  /v2           Veronica-2 Search
[INF]                ────────────────────
[INF]                Last updated: 2024-01
```

### Step 2: Fetch a text file

```bash
mototli text gopher.floodgap.com /gopher/welcome
```

### Step 3: Get Gopher+ attributes

```bash
mototli attrs gopher.floodgap.com /gopher
```

!!! tip "Verbose output"
    Add `--verbose` to see the raw protocol exchange:
    ```bash
    mototli get gopher.floodgap.com --verbose
    ```

---

## Scenario 2: Serve a Gopherhole

Host your own gopher content in under a minute.

### Step 1: Create a content directory

```bash
mkdir my-gopherhole
cd my-gopherhole
```

### Step 2: Add a welcome file

Create `index.txt`:

```
Welcome to my gopherhole!

This is served by Mototli.
```

### Step 3: Start the server

```bash
mototli serve . --port 7070
```

You'll see:

```
Starting Gopher server...
  Document root: /path/to/my-gopherhole
  Listening on: localhost:7070
  Gopher+ enabled: Yes
```

### Step 4: Browse your site

In another terminal:

```bash
mototli get localhost:7070
```

!!! note "Default port"
    Gopher's default port is 70, which requires root privileges on Unix systems.
    Use `--port 7070` or another high port for development.

---

## Scenario 3: Use the Python Client

Integrate Gopher access into your Python applications.

### Step 1: Create a script

Create `browse.py`:

```python
import asyncio
from mototli.client import GopherClient

async def main():
    async with GopherClient(timeout=30.0) as client:
        # Fetch a directory listing
        response = await client.get("gopher.floodgap.com", "/")

        print("=== Directory Listing ===")
        for item in response.items:
            if item.item_type.is_informational:
                print(f"     {item.display_text}")
            else:
                print(f"[{item.item_type.value}] {item.display_text}")
                print(f"     -> {item.selector}")

asyncio.run(main())
```

### Step 2: Run it

```bash
python browse.py
```

### Step 3: Fetch text content

```python
async def fetch_text():
    async with GopherClient() as client:
        response = await client.get_text("gopher.floodgap.com", "/gopher/welcome")
        print(response.content.decode())

asyncio.run(fetch_text())
```

### Step 4: Handle binary files

```python
async def fetch_binary():
    async with GopherClient() as client:
        response = await client.get_binary("gopher.floodgap.com", "/gopher/logo.gif")

        with open("logo.gif", "wb") as f:
            f.write(response.content)
        print(f"Saved {len(response.content)} bytes")

asyncio.run(fetch_binary())
```

---

## Common Issues

### Connection refused

```
Error: Connection refused to localhost:70
```

**Solution**: The server isn't running, or you need to specify the correct port:

```bash
mototli get localhost:7070
```

### Timeout errors

```
Error: Connection timed out
```

**Solution**: The server may be slow or unreachable. Increase the timeout:

```bash
mototli get slow-server.example --timeout 60
```

### Port permission denied

```
Error: Permission denied for port 70
```

**Solution**: Port 70 requires root privileges. Use a high port:

```bash
mototli serve . --port 7070
```

---

## Recommended Learning Paths

Choose based on your goals:

### I want to host a gopherhole

1. [:octicons-arrow-right-24: Your First Gopherhole](tutorials/your-first-gopherhole.md) - Complete server tutorial
2. [:octicons-arrow-right-24: Configure Server](how-to/configure-server.md) - TOML configuration
3. [:octicons-arrow-right-24: Setup CGI](how-to/setup-cgi.md) - Dynamic content

### I want to build a gopher client

1. [:octicons-arrow-right-24: Building a Client](tutorials/building-a-client.md) - Client tutorial
2. [:octicons-arrow-right-24: Fetch Resources](how-to/fetch-resources.md) - Advanced fetching
3. [:octicons-arrow-right-24: Client API](reference/api/client.md) - Full API reference

### I want to understand the protocol

1. [:octicons-arrow-right-24: Gopher Protocol](explanation/gopher-protocol.md) - Protocol deep-dive
2. [:octicons-arrow-right-24: Gopher+ Extensions](explanation/gopher-plus.md) - RFC 4266
3. [:octicons-arrow-right-24: Item Types](reference/item-types.md) - Type reference

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/alanbato/mototli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/alanbato/mototli/discussions)
