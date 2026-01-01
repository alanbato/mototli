# Configuration Reference

Complete reference for Mototli server TOML configuration.

## Configuration File

Create a TOML file (e.g., `server.toml`) with your settings:

```bash
mototli serve --config server.toml
```

Generate a template:

```bash
mototli serve --init > server.toml
```

---

## [server]

Core server settings.

```toml
[server]
host = "0.0.0.0"
port = 70
hostname = "gopher.example.com"
document_root = "/var/gopher"
```

### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `host` | string | IP address to bind to | `"localhost"` |
| `port` | integer | Port number (1-65535) | `70` |
| `hostname` | string | Public hostname for directory listings | value of `host` |
| `document_root` | string | Directory to serve files from | `"."` |

### Notes

- Use `"0.0.0.0"` to listen on all interfaces
- Port 70 requires root privileges on Unix
- `hostname` should be the public-facing hostname clients will use

---

## [handlers]

File serving and handler configuration.

```toml
[handlers]
enable_directory_listing = true
default_indices = ["gophermap", "index.gph", "index.txt"]
max_file_size = 104857600
cgi_extensions = [".cgi", ".sh", ".py", ".pl"]
cgi_directories = ["cgi-bin"]
```

### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `enable_directory_listing` | boolean | Auto-generate listings for directories without gophermap | `true` |
| `default_indices` | array | Files to use as directory index (in order) | `["gophermap", "index.gph"]` |
| `max_file_size` | integer | Maximum file size in bytes | `104857600` (100 MiB) |
| `cgi_extensions` | array | File extensions to execute as CGI | `[".cgi"]` |
| `cgi_directories` | array | Directories where CGI is allowed | `["cgi-bin"]` |

### Directory Index Resolution

When a directory is requested, the server looks for index files in order:

1. Check each file in `default_indices`
2. First existing file is served
3. If none found and `enable_directory_listing` is true, generate listing
4. Otherwise, return error

### CGI Execution

Files are executed as CGI when:

1. File extension is in `cgi_extensions`, AND
2. File is in a directory listed in `cgi_directories` (or subdirectory)

---

## [gopher_plus]

Gopher+ extension settings.

```toml
[gopher_plus]
enabled = true
admin_name = "Server Administrator"
admin_email = "admin@example.com"
```

### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `enabled` | boolean | Enable Gopher+ support | `true` |
| `admin_name` | string | Administrator name for +ADMIN block | `""` |
| `admin_email` | string | Administrator email for +ADMIN block | `""` |

### Gopher+ Features

When enabled:

- Responds to attribute queries (`$` modifier)
- Supports view requests (`+` modifier)
- Includes +INFO, +ADMIN, +VIEWS blocks
- Reports file sizes in attributes

---

## [limits]

Resource limits and timeouts.

```toml
[limits]
request_timeout = 30.0
cgi_timeout = 30.0
```

### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `request_timeout` | float | Maximum time for handling a request (seconds) | `30.0` |
| `cgi_timeout` | float | Maximum CGI script execution time (seconds) | `30.0` |

---

## Complete Example

```toml
# Mototli Server Configuration

[server]
# Network settings
host = "0.0.0.0"              # Listen on all interfaces
port = 70                      # Standard Gopher port
hostname = "gopher.example.com" # Public hostname

# Content
document_root = "/var/gopher"  # Root directory

[handlers]
# Directory listings
enable_directory_listing = true
default_indices = ["gophermap", "index.gph", "index.txt"]

# File limits
max_file_size = 104857600      # 100 MiB

# CGI settings
cgi_extensions = [".cgi", ".sh", ".py", ".pl"]
cgi_directories = ["cgi-bin", "scripts"]

[gopher_plus]
# Enable Gopher+ extensions
enabled = true

# Admin information (shown in +ADMIN block)
admin_name = "Site Administrator"
admin_email = "admin@example.com"

[limits]
# Timeouts
request_timeout = 30.0         # Request handling timeout
cgi_timeout = 30.0             # CGI execution timeout
```

---

## Loading Configuration

### From Python

```python
from mototli.server import ServerConfig

# From file
config = ServerConfig.from_toml("server.toml")

# Validate
config.validate()

# Access settings
print(config.host)
print(config.port)
print(config.document_root)
```

### Programmatic Configuration

```python
from mototli.server import ServerConfig, GopherServer
from pathlib import Path

config = ServerConfig(
    host="0.0.0.0",
    port=7070,
    hostname="localhost",
    document_root=Path("./content"),
    gopher_plus=True,
    admin_name="Admin",
    admin_email="admin@example.com"
)

server = GopherServer(config)
```

---

## Configuration Validation

The server validates configuration on startup:

| Check | Error |
|-------|-------|
| Port out of range | "Port must be between 1 and 65535" |
| Document root doesn't exist | "Document root does not exist" |
| Invalid timeout | "Timeout must be positive" |

---

## See Also

- [:octicons-arrow-right-24: Configure Server](../how-to/configure-server.md) - How-to guide
- [:octicons-arrow-right-24: CLI Reference](cli.md) - Command-line options
- [:octicons-arrow-right-24: Server API](api/server.md) - ServerConfig class
