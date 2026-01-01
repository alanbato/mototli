# Installation

This guide covers how to install Mototli for both usage and development.

## Prerequisites

- **Python 3.10 or higher** (3.12+ recommended)
- A package manager: `uv`, `pipx`, or `pip`

## Installation Methods

=== "uv (Recommended)"

    [uv](https://docs.astral.sh/uv/) is the recommended package manager for its speed and reliability.

    ```bash
    # Add to an existing project
    uv add mototli

    # Or install globally
    uv tool install mototli
    ```

=== "pipx"

    Use [pipx](https://pypa.github.io/pipx/) to install Mototli as a CLI tool in an isolated environment.

    ```bash
    pipx install mototli
    ```

=== "pip"

    Install with pip into your current environment.

    ```bash
    pip install mototli
    ```

=== "From Source"

    Install the latest development version from GitHub.

    ```bash
    git clone https://github.com/alanbato/mototli.git
    cd mototli
    uv sync
    ```

## Verification

Verify your installation by checking the version:

```bash
mototli version
```

You should see output like:

```
Mototli v0.1.0
Protocol: Gopher (RFC 1436) with Gopher+ (RFC 4266)
```

Try fetching a resource from a public gopher server:

```bash
mototli get gopher.floodgap.com
```

## Shell Completion

Mototli uses [Typer](https://typer.tiangolo.com/) for its CLI, which supports shell completion.

=== "Bash"

    ```bash
    # Add to ~/.bashrc
    eval "$(mototli --show-completion bash)"
    ```

=== "Zsh"

    ```bash
    # Add to ~/.zshrc
    eval "$(mototli --show-completion zsh)"
    ```

=== "Fish"

    ```bash
    # Add to ~/.config/fish/config.fish
    mototli --show-completion fish | source
    ```

## Development Setup

For contributing to Mototli or developing with the source code:

```bash
# Clone the repository
git clone https://github.com/alanbato/mototli.git
cd mototli

# Install all dependencies (including dev tools)
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/
```

## Dependencies

Mototli has minimal runtime dependencies:

| Package | Purpose |
|---------|---------|
| `rich` | Terminal formatting and colors |
| `structlog` | Structured logging |
| `typer` | Command-line interface |
| `tomli` | TOML parsing (Python < 3.11) |

## Troubleshooting

### Command not found

If `mototli` is not found after installation:

1. Ensure the installation location is in your `PATH`
2. For `pipx`, run `pipx ensurepath`
3. For `uv tool`, run `uv tool update-shell`

### Permission errors

If you encounter permission errors:

- Use `uv` or `pipx` instead of `pip` for system-wide installs
- Or use a virtual environment: `python -m venv .venv && source .venv/bin/activate`

### Import errors

If you can run `mototli` but cannot import the library:

```bash
# Ensure you're in the correct environment
which python
pip show mototli
```

## Next Steps

- [:octicons-arrow-right-24: Quick Start Guide](quickstart.md) - Get up and running quickly
- [:octicons-arrow-right-24: Your First Gopherhole](tutorials/your-first-gopherhole.md) - Serve your first content
- [:octicons-arrow-right-24: CLI Reference](reference/cli.md) - Explore all CLI commands
