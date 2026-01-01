"""Tests for ServerConfig."""

from pathlib import Path

import pytest

from mototli.protocol.constants import DEFAULT_PORT, REQUEST_TIMEOUT
from mototli.server.config import ServerConfig


class TestServerConfigCreation:
    """Tests for ServerConfig initialization."""

    def test_default_values(self, tmp_path: Path):
        """Default config has expected values."""
        config = ServerConfig(document_root=tmp_path)

        assert config.host == "localhost"
        assert config.port == DEFAULT_PORT
        assert config.enable_directory_listing is True
        assert config.gopher_plus is True
        assert config.request_timeout == REQUEST_TIMEOUT
        assert config.cgi_timeout == 30.0
        assert config.max_file_size == 100 * 1024 * 1024

    def test_custom_values(self, tmp_path: Path):
        """Config accepts custom values for all fields."""
        config = ServerConfig(
            host="0.0.0.0",
            port=7070,
            document_root=tmp_path,
            hostname="gopher.example.com",
            enable_directory_listing=False,
            gopher_plus=False,
            admin_name="Admin",
            admin_email="admin@example.com",
            request_timeout=60.0,
            cgi_timeout=10.0,
            max_file_size=50 * 1024 * 1024,
        )

        assert config.host == "0.0.0.0"
        assert config.port == 7070
        assert config.hostname == "gopher.example.com"
        assert config.enable_directory_listing is False
        assert config.gopher_plus is False
        assert config.admin_name == "Admin"
        assert config.admin_email == "admin@example.com"
        assert config.request_timeout == 60.0
        assert config.cgi_timeout == 10.0
        assert config.max_file_size == 50 * 1024 * 1024

    def test_document_root_string_conversion(self, tmp_path: Path):
        """String document_root is converted to Path."""
        config = ServerConfig(document_root=str(tmp_path))

        assert isinstance(config.document_root, Path)
        assert config.document_root == tmp_path

    def test_document_root_resolved(self, tmp_path: Path):
        """Document root is resolved to absolute path."""
        # Create a relative path scenario
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        config = ServerConfig(document_root=subdir)

        assert config.document_root.is_absolute()
        assert config.document_root == subdir.resolve()

    def test_hostname_defaults_to_host(self, tmp_path: Path):
        """If hostname is None, it defaults to host."""
        config = ServerConfig(host="myhost.local", document_root=tmp_path)

        assert config.hostname == "myhost.local"

    def test_explicit_hostname(self, tmp_path: Path):
        """Explicit hostname overrides host."""
        config = ServerConfig(
            host="127.0.0.1",
            hostname="gopher.example.com",
            document_root=tmp_path,
        )

        assert config.hostname == "gopher.example.com"

    def test_default_indices(self, tmp_path: Path):
        """Default index files list is set."""
        config = ServerConfig(document_root=tmp_path)

        assert "index.gph" in config.default_indices
        assert "gophermap" in config.default_indices
        assert "index.txt" in config.default_indices

    def test_custom_indices(self, tmp_path: Path):
        """Custom index files list is accepted."""
        custom = ["home.gph", "welcome.txt"]
        config = ServerConfig(document_root=tmp_path, default_indices=custom)

        assert config.default_indices == custom

    def test_default_cgi_extensions(self, tmp_path: Path):
        """Default CGI extensions are set."""
        config = ServerConfig(document_root=tmp_path)

        assert ".cgi" in config.cgi_extensions
        assert ".py" in config.cgi_extensions
        assert ".sh" in config.cgi_extensions
        assert ".pl" in config.cgi_extensions

    def test_default_cgi_directories(self, tmp_path: Path):
        """Default CGI directories are set."""
        config = ServerConfig(document_root=tmp_path)

        assert "cgi-bin" in config.cgi_directories


class TestServerConfigValidation:
    """Tests for ServerConfig.validate()."""

    def test_valid_config_passes(self, populated_document_root: Path):
        """Valid configuration passes validation."""
        config = ServerConfig(document_root=populated_document_root)

        # Should not raise
        config.validate()

    def test_missing_document_root_raises(self, tmp_path: Path):
        """Non-existent document root raises ValueError."""
        config = ServerConfig(document_root=tmp_path / "nonexistent")

        with pytest.raises(ValueError, match="Document root does not exist"):
            config.validate()

    def test_file_as_document_root_raises(self, tmp_path: Path):
        """File path as document root raises ValueError."""
        file = tmp_path / "file.txt"
        file.write_text("content")
        config = ServerConfig(document_root=file)

        with pytest.raises(ValueError, match="Document root is not a directory"):
            config.validate()

    @pytest.mark.parametrize("port", [0, -1, 65536, 100000])
    def test_invalid_port_raises(self, port: int, tmp_path: Path):
        """Invalid port values raise ValueError."""
        config = ServerConfig(document_root=tmp_path, port=port)

        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            config.validate()

    @pytest.mark.parametrize("port", [1, 70, 7070, 65535])
    def test_valid_port_range(self, port: int, tmp_path: Path):
        """Valid ports (1-65535) pass validation."""
        config = ServerConfig(document_root=tmp_path, port=port)

        # Should not raise
        config.validate()

    @pytest.mark.parametrize("timeout", [0, -1, -0.5])
    def test_invalid_request_timeout_raises(self, timeout: float, tmp_path: Path):
        """Non-positive request timeout raises ValueError."""
        config = ServerConfig(document_root=tmp_path, request_timeout=timeout)

        with pytest.raises(ValueError, match="Request timeout must be positive"):
            config.validate()

    @pytest.mark.parametrize("timeout", [0, -1, -0.5])
    def test_invalid_cgi_timeout_raises(self, timeout: float, tmp_path: Path):
        """Non-positive CGI timeout raises ValueError."""
        config = ServerConfig(document_root=tmp_path, cgi_timeout=timeout)

        with pytest.raises(ValueError, match="CGI timeout must be positive"):
            config.validate()

    def test_invalid_max_file_size_raises(self, tmp_path: Path):
        """Non-positive max file size raises ValueError."""
        config = ServerConfig(document_root=tmp_path, max_file_size=0)

        with pytest.raises(ValueError, match="Max file size must be positive"):
            config.validate()


class TestServerConfigToml:
    """Tests for TOML serialization/deserialization."""

    def test_from_toml_basic(self, tmp_path: Path):
        """Load basic configuration from TOML file."""
        doc_root = tmp_path / "gopher"
        doc_root.mkdir()

        config_file = tmp_path / "config.toml"
        config_file.write_text(f"""
[server]
host = "0.0.0.0"
port = 7070
document_root = "{doc_root}"
""")

        config = ServerConfig.from_toml(config_file)

        assert config.host == "0.0.0.0"
        assert config.port == 7070
        assert config.document_root == doc_root

    def test_from_toml_all_sections(self, tmp_path: Path):
        """Load configuration with all TOML sections."""
        doc_root = tmp_path / "gopher"
        doc_root.mkdir()

        config_file = tmp_path / "config.toml"
        config_file.write_text(f"""
[server]
host = "0.0.0.0"
port = 7070
document_root = "{doc_root}"
hostname = "gopher.example.com"

[handlers]
enable_directory_listing = false
default_indices = ["index.gph", "welcome.txt"]
cgi_extensions = [".cgi", ".sh"]
cgi_directories = ["cgi-bin", "scripts"]

[gopher_plus]
enabled = true
admin_name = "Admin User"
admin_email = "admin@example.com"

[limits]
max_file_size = 52428800
request_timeout = 60.0
cgi_timeout = 15.0
""")

        config = ServerConfig.from_toml(config_file)

        assert config.hostname == "gopher.example.com"
        assert config.enable_directory_listing is False
        assert config.default_indices == ["index.gph", "welcome.txt"]
        assert config.cgi_extensions == [".cgi", ".sh"]
        assert config.cgi_directories == ["cgi-bin", "scripts"]
        assert config.gopher_plus is True
        assert config.admin_name == "Admin User"
        assert config.admin_email == "admin@example.com"
        assert config.max_file_size == 52428800
        assert config.request_timeout == 60.0
        assert config.cgi_timeout == 15.0

    def test_from_toml_missing_file_raises(self, tmp_path: Path):
        """Missing TOML file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            ServerConfig.from_toml(tmp_path / "nonexistent.toml")

    def test_to_toml_roundtrip(self, tmp_path: Path):
        """Config serialized to TOML can be deserialized back."""
        original = ServerConfig(
            host="0.0.0.0",
            port=7070,
            document_root=tmp_path,
            hostname="gopher.example.com",
            gopher_plus=True,
            admin_name="Admin",
            admin_email="admin@example.com",
        )

        # Write to file
        toml_str = original.to_toml()
        config_file = tmp_path / "config.toml"
        config_file.write_text(toml_str)

        # Read back
        loaded = ServerConfig.from_toml(config_file)

        assert loaded.host == original.host
        assert loaded.port == original.port
        assert loaded.hostname == original.hostname
        assert loaded.gopher_plus == original.gopher_plus
        assert loaded.admin_name == original.admin_name
        assert loaded.admin_email == original.admin_email

    def test_to_toml_includes_all_fields(self, tmp_path: Path):
        """Generated TOML includes all configuration fields."""
        config = ServerConfig(
            host="0.0.0.0",
            port=7070,
            document_root=tmp_path,
            hostname="test.host",
            admin_name="Admin",
            admin_email="admin@test.com",
        )

        toml_str = config.to_toml()

        assert "[server]" in toml_str
        assert 'host = "0.0.0.0"' in toml_str
        assert "port = 7070" in toml_str
        assert "[handlers]" in toml_str
        assert "[gopher_plus]" in toml_str
        assert "[limits]" in toml_str
        assert 'admin_name = "Admin"' in toml_str


class TestServerConfigProperties:
    """Tests for ServerConfig properties."""

    def test_public_hostname(self, tmp_path: Path):
        """public_hostname returns hostname or host."""
        config = ServerConfig(
            host="127.0.0.1",
            hostname="gopher.example.com",
            document_root=tmp_path,
        )

        assert config.public_hostname == "gopher.example.com"

    def test_public_hostname_defaults_to_host(self, tmp_path: Path):
        """public_hostname returns host when hostname is not set."""
        # When hostname is None, __post_init__ sets it to host
        config = ServerConfig(host="myhost.local", document_root=tmp_path)

        assert config.public_hostname == "myhost.local"

    def test_public_port(self, tmp_path: Path):
        """public_port returns the configured port."""
        config = ServerConfig(document_root=tmp_path, port=7070)

        assert config.public_port == 7070
