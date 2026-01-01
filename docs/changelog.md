# Changelog

All notable changes to Mototli will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial documentation with Diataxis structure

## [0.1.0] - 2025-01-01

### Added

- **Protocol Module**: Complete Gopher protocol implementation (RFC 1436)
  - `ItemType` enum with 25+ item types
  - `GopherRequest` and `GopherResponse` dataclasses
  - Request parsing and serialization

- **Gopher+ Extensions** (RFC 4266)
  - `GopherAttributes` for attribute block parsing
  - Support for `$`, `+`, and `!` request modifiers
  - `+INFO`, `+ADMIN`, `+VIEWS`, `+ABSTRACT` blocks

- **Async Client**
  - `GopherClient` with context manager support
  - `get()`, `get_text()`, `get_binary()` methods
  - `get_attributes()` for Gopher+ queries
  - Configurable timeout handling

- **Async Server**
  - `GopherServer` with full Gopher+ support
  - Static file serving with automatic MIME detection
  - Automatic directory listing generation
  - CGI script execution (.cgi, .sh, .py, .pl)
  - TOML configuration file support
  - Request routing with exact and prefix matching

- **CLI Tool**
  - `mototli get` - Fetch Gopher resources
  - `mototli text` - Fetch text files
  - `mototli attrs` - Get Gopher+ attributes
  - `mototli serve` - Start a Gopher server
  - `mototli version` - Show version info
  - Rich terminal output with colors

- **Utilities**
  - MIME type detection from file extensions
  - Item type inference from MIME types

[Unreleased]: https://github.com/alanbato/mototli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alanbato/mototli/releases/tag/v0.1.0
