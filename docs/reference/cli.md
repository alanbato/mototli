# CLI Reference

Complete reference for the `mototli` command-line interface.

## Global Options

```bash
mototli [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version (alias for `version` command) |

---

## Commands

### mototli get

Fetch and display a Gopher resource.

```bash
mototli get [OPTIONS] HOST [SELECTOR]
```

#### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `HOST` | Server hostname (required) | - |
| `SELECTOR` | Resource selector path | `/` |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port`, `-p` | Server port | `70` |
| `--search`, `-s` | Search query (for type 7 items) | - |
| `--type`, `-t` | Item type (`0`=text, `1`=dir, `7`=search, `9`=binary) | auto |
| `--timeout` | Connection timeout in seconds | `30.0` |
| `--verbose`, `-v` | Show detailed output with protocol info | `false` |
| `--raw`, `-r` | Output raw response (no formatting) | `false` |

#### Examples

```bash
# Fetch root directory
mototli get gopher.floodgap.com

# Fetch specific path
mototli get gopher.floodgap.com /gopher

# Custom port
mototli get localhost --port 7070

# Search query
mototli get gopher.floodgap.com /v2/vs --search "python"

# Force text type
mototli get example.com /file --type 0

# Verbose output
mototli get gopher.floodgap.com --verbose

# Raw output (for piping)
mototli get gopher.floodgap.com /file.txt --raw > file.txt
```

---

### mototli text

Fetch and display a text file (convenience command for type 0).

```bash
mototli text [OPTIONS] HOST SELECTOR
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `HOST` | Server hostname (required) |
| `SELECTOR` | File selector path (required) |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port`, `-p` | Server port | `70` |
| `--timeout` | Connection timeout in seconds | `30.0` |

#### Examples

```bash
# Fetch a text file
mototli text gopher.floodgap.com /gopher/welcome

# Custom port
mototli text localhost /readme.txt --port 7070
```

---

### mototli attrs

Fetch Gopher+ attributes for a resource.

```bash
mototli attrs [OPTIONS] HOST [SELECTOR]
```

#### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `HOST` | Server hostname (required) | - |
| `SELECTOR` | Resource selector path | `/` |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port`, `-p` | Server port | `70` |
| `--timeout` | Connection timeout in seconds | `30.0` |

#### Output

Displays formatted attribute blocks:

- `+INFO` - Item information
- `+ADMIN` - Administrator contact
- `+VIEWS` - Available content types
- `+ABSTRACT` - Item description

#### Examples

```bash
# Get attributes for root
mototli attrs gopher.floodgap.com

# Get attributes for specific item
mototli attrs gopher.floodgap.com /gopher/welcome

# Custom port
mototli attrs localhost /document --port 7070
```

---

### mototli serve

Start a Gopher server.

```bash
mototli serve [OPTIONS] [ROOT]
```

#### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `ROOT` | Document root directory | `.` |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | IP address to bind to | `localhost` |
| `--port`, `-p` | Port to listen on | `70` |
| `--hostname` | Public hostname for listings | value of `--host` |
| `--no-directory-listing` | Disable auto directory listings | `false` |
| `--no-gopher-plus` | Disable Gopher+ support | `false` |
| `--admin-name` | Administrator name for Gopher+ | - |
| `--admin-email` | Administrator email for Gopher+ | - |
| `--config`, `-c` | Load settings from TOML file | - |
| `--init` | Print example configuration and exit | `false` |

#### Examples

```bash
# Serve current directory on port 7070
mototli serve --port 7070

# Serve specific directory
mototli serve /var/gopher --port 70

# With public hostname
mototli serve /var/gopher --hostname gopher.example.com

# With admin info
mototli serve . --admin-name "Your Name" --admin-email "you@example.com"

# Disable auto listings
mototli serve . --no-directory-listing

# Use configuration file
mototli serve --config server.toml

# Generate example config
mototli serve --init > server.toml
```

#### Startup Output

```
Starting Gopher server...
  Document root: /path/to/content
  Listening on: localhost:7070
  Hostname: localhost
  Gopher+ enabled: Yes

Press Ctrl+C to stop
```

---

### mototli version

Show version and protocol information.

```bash
mototli version
```

#### Output

```
Mototli v0.1.0
Protocol: Gopher (RFC 1436) with Gopher+ (RFC 4266)
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Connection error (timeout, refused, etc.) |

---

## Environment Variables

Mototli respects standard terminal settings:

| Variable | Effect |
|----------|--------|
| `NO_COLOR` | Disable colored output |
| `FORCE_COLOR` | Force colored output |
| `TERM` | Terminal type for formatting |

---

## Shell Completion

Generate shell completion scripts:

```bash
# Bash
mototli --show-completion bash >> ~/.bashrc

# Zsh
mototli --show-completion zsh >> ~/.zshrc

# Fish
mototli --show-completion fish > ~/.config/fish/completions/mototli.fish
```

---

## See Also

- [:octicons-arrow-right-24: Quick Start](../quickstart.md) - Getting started
- [:octicons-arrow-right-24: Configuration](configuration.md) - TOML config reference
- [:octicons-arrow-right-24: Configure Server](../how-to/configure-server.md) - Server setup guide
