# Setup CGI

This guide shows how to configure and write CGI scripts for dynamic content.

## Prerequisites

- Mototli [installed](../installation.md)
- A server [configured](configure-server.md)
- Basic shell scripting knowledge

## Enable CGI support

Add CGI settings to your `server.toml`:

```toml
[handlers]
cgi_extensions = [".cgi", ".sh", ".py", ".pl"]
cgi_directories = ["cgi-bin"]
cgi_timeout = 30.0
```

### Options

| Option | Description |
|--------|-------------|
| `cgi_extensions` | File extensions to execute as CGI |
| `cgi_directories` | Directories where CGI is allowed |
| `cgi_timeout` | Maximum script execution time (seconds) |

## Create a CGI directory

```bash
mkdir -p my-gopherhole/cgi-bin
```

## Write a simple CGI script

Create `cgi-bin/hello.cgi`:

```bash
#!/bin/bash
echo "Hello from CGI!"
echo ""
echo "Current time: $(date)"
echo "Your request: $SELECTOR"
```

Make it executable:

```bash
chmod +x my-gopherhole/cgi-bin/hello.cgi
```

## Test your script

Start the server:

```bash
mototli serve my-gopherhole --port 7070
```

Fetch the CGI output:

```bash
mototli text localhost:7070 /cgi-bin/hello.cgi
```

## CGI environment variables

Mototli provides these environment variables to CGI scripts:

| Variable | Description |
|----------|-------------|
| `SELECTOR` | The requested selector path |
| `QUERY_STRING` | Search query (for type 7 searches) |
| `SERVER_NAME` | Server hostname |
| `SERVER_PORT` | Server port |
| `REMOTE_HOST` | Client IP address |
| `GOPHER_PLUS` | `1` if Gopher+ request, `0` otherwise |
| `SCRIPT_NAME` | Path to the script |
| `DOCUMENT_ROOT` | Server document root |

## Python CGI example

Create `cgi-bin/info.py`:

```python
#!/usr/bin/env python3
import os
import sys

print("=== Gopher CGI Info ===")
print()
print(f"Selector: {os.environ.get('SELECTOR', '(none)')}")
print(f"Query: {os.environ.get('QUERY_STRING', '(none)')}")
print(f"Server: {os.environ.get('SERVER_NAME', '?')}:{os.environ.get('SERVER_PORT', '?')}")
print(f"Client: {os.environ.get('REMOTE_HOST', '?')}")
print(f"Gopher+: {'Yes' if os.environ.get('GOPHER_PLUS') == '1' else 'No'}")
print()
print("=== All Environment ===")
for key, value in sorted(os.environ.items()):
    if key.startswith(('GOPHER', 'SERVER', 'REMOTE', 'QUERY', 'SELECTOR', 'SCRIPT', 'DOCUMENT')):
        print(f"{key}={value}")
```

Make it executable:

```bash
chmod +x my-gopherhole/cgi-bin/info.py
```

## Handle search queries

Gopher type 7 items (search) pass the query via `QUERY_STRING`.

Create `cgi-bin/search.py`:

```python
#!/usr/bin/env python3
import os

query = os.environ.get('QUERY_STRING', '')

if not query:
    print("Enter a search term:")
    print("")
    print("Usage: Select this item and enter your query")
else:
    print(f"Searching for: {query}")
    print("")
    # Simulate search results
    results = [
        f"Result 1 for '{query}'",
        f"Result 2 for '{query}'",
        f"Result 3 for '{query}'",
    ]
    for result in results:
        print(result)
```

Add a search item to your gophermap:

```
7Search my site	/cgi-bin/search.py	localhost	7070
```

## Generate directory listings

Create `cgi-bin/listing.py` to generate dynamic gophermaps:

```python
#!/usr/bin/env python3
import os
from datetime import datetime

print(f"iDynamic Directory Listing\tfake\t(NULL)\t0")
print(f"iGenerated: {datetime.now()}\tfake\t(NULL)\t0")
print(f"i\tfake\t(NULL)\t0")

doc_root = os.environ.get('DOCUMENT_ROOT', '.')
for item in sorted(os.listdir(doc_root)):
    path = os.path.join(doc_root, item)
    if os.path.isdir(path):
        print(f"1{item}\t/{item}\tlocalhost\t7070")
    elif item.endswith(('.txt', '.md')):
        print(f"0{item}\t/{item}\tlocalhost\t7070")
```

## Security considerations

!!! warning "CGI Security"
    CGI scripts run with server privileges. Follow these practices:

1. **Restrict CGI directories**: Only enable CGI in specific directories
2. **Validate input**: Never trust `SELECTOR` or `QUERY_STRING` directly
3. **Set timeouts**: Use `cgi_timeout` to prevent runaway scripts
4. **Limit permissions**: Run scripts with minimal privileges

### Input validation example

```python
#!/usr/bin/env python3
import os
import re

query = os.environ.get('QUERY_STRING', '')

# Validate input - only allow alphanumeric and spaces
if not re.match(r'^[\w\s]*$', query):
    print("Error: Invalid search query")
    exit(1)

# Safe to use query now
print(f"Searching for: {query}")
```

## Debugging CGI

Test scripts directly:

```bash
# Set environment variables
export SELECTOR="/cgi-bin/test.cgi"
export QUERY_STRING="test query"
export SERVER_NAME="localhost"
export SERVER_PORT="7070"

# Run the script
./cgi-bin/test.cgi
```

Check server logs for errors:

```bash
mototli serve my-gopherhole --port 7070 2>&1 | tee server.log
```

## See also

- [:octicons-arrow-right-24: Configure Server](configure-server.md) - Server configuration
- [:octicons-arrow-right-24: Directory Listings](directory-listings.md) - Static gophermaps
- [:octicons-arrow-right-24: CLI Reference](../reference/cli.md) - Server options
