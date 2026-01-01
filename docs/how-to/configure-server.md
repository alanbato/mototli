# Configure Server

This guide shows how to configure the Mototli server using TOML configuration files.

## Prerequisites

- Mototli [installed](../installation.md)
- A content directory to serve

## Generate a configuration template

Use the `--init` flag to generate a template:

```bash
mototli serve --init > server.toml
```

This creates a configuration file with all available options and their defaults.

## Basic configuration

Create `server.toml`:

```toml
[server]
host = "0.0.0.0"
port = 70
hostname = "gopher.example.com"
document_root = "/var/gopher"
```

### Configuration options

| Option | Description | Default |
|--------|-------------|---------|
| `host` | IP address to bind to | `"localhost"` |
| `port` | Port number | `70` |
| `hostname` | Public hostname for directory listings | `"localhost"` |
| `document_root` | Directory to serve files from | `"."` |

## Start with configuration

```bash
mototli serve --config server.toml
```

## Handler configuration

Configure how files are served:

```toml
[handlers]
enable_directory_listing = true
default_indices = ["gophermap", "index.gph", "index.txt"]
max_file_size = 104857600  # 100 MiB
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `enable_directory_listing` | Auto-generate listings | `true` |
| `default_indices` | Files to look for as directory index | `["gophermap", "index.gph"]` |
| `max_file_size` | Maximum file size to serve (bytes) | `104857600` |

## CGI configuration

Enable CGI script execution:

```toml
[handlers]
cgi_extensions = [".cgi", ".sh", ".py", ".pl"]
cgi_directories = ["cgi-bin"]
cgi_timeout = 30.0
```

See [Setup CGI](setup-cgi.md) for detailed CGI configuration.

## Gopher+ configuration

Configure Gopher+ extensions:

```toml
[gopher_plus]
enabled = true
admin_name = "Your Name"
admin_email = "admin@example.com"
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `enabled` | Enable Gopher+ support | `true` |
| `admin_name` | Administrator name for +ADMIN | `""` |
| `admin_email` | Administrator email for +ADMIN | `""` |

## Timeout configuration

```toml
[limits]
request_timeout = 30.0
cgi_timeout = 30.0
```

## Complete example

```toml
# server.toml - Complete Mototli configuration

[server]
host = "0.0.0.0"
port = 70
hostname = "gopher.example.com"
document_root = "/var/gopher"

[handlers]
enable_directory_listing = true
default_indices = ["gophermap", "index.gph", "index.txt"]
max_file_size = 104857600
cgi_extensions = [".cgi", ".sh", ".py"]
cgi_directories = ["cgi-bin"]

[gopher_plus]
enabled = true
admin_name = "Server Admin"
admin_email = "admin@example.com"

[limits]
request_timeout = 30.0
cgi_timeout = 30.0
```

## Verify configuration

Use verbose mode to verify settings:

```bash
mototli serve --config server.toml
```

The startup message shows applied settings:

```
Starting Gopher server...
  Document root: /var/gopher
  Listening on: 0.0.0.0:70
  Hostname: gopher.example.com
  Gopher+ enabled: Yes
  Admin: Server Admin <admin@example.com>
```

## Environment-specific configs

Create different configs for different environments:

```bash
# Development
mototli serve --config server.dev.toml

# Production
mototli serve --config server.prod.toml
```

## See also

- [:octicons-arrow-right-24: Configuration Reference](../reference/configuration.md) - All options
- [:octicons-arrow-right-24: Setup CGI](setup-cgi.md) - CGI configuration details
- [:octicons-arrow-right-24: CLI Reference](../reference/cli.md) - Command-line options
