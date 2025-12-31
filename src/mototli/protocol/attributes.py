"""Gopher+ attribute blocks.

This module provides parsing and generation of Gopher+ attribute blocks
as defined in RFC 4266.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from .constants import (
    ATTR_ABSTRACT,
    ATTR_ADMIN,
    ATTR_ASK,
    ATTR_INFO,
    ATTR_VIEWS,
)

if TYPE_CHECKING:
    from .response import GopherItem


@dataclass
class ViewInfo:
    """Represents a single view/representation in Gopher+.

    Attributes:
        mime_type: The MIME type of this view.
        language: Optional language code.
        size: Optional size in bytes (as string with units like "<10k>").
        size_bytes: Parsed size in bytes (if available).
    """

    mime_type: str
    language: str | None = None
    size: str | None = None
    size_bytes: int | None = None

    @classmethod
    def parse(cls, line: str) -> ViewInfo:
        """Parse a view line from Gopher+ VIEWS block.

        Format: MIME/type [language]: <size>

        Args:
            line: A single view specification line.

        Returns:
            A ViewInfo instance.

        Examples:
            >>> view = ViewInfo.parse("text/plain: <10k>")
            >>> view.mime_type
            'text/plain'
        """
        line = line.strip()

        # Extract size if present
        size: str | None = None
        size_bytes: int | None = None
        size_match = re.search(r"<([^>]+)>", line)
        if size_match:
            size = size_match.group(1)
            size_bytes = _parse_size(size)
            line = line[: size_match.start()].strip()

        # Split MIME type and language
        parts = line.split()
        mime_type = parts[0].rstrip(":") if parts else "application/octet-stream"
        language = parts[1].rstrip(":") if len(parts) > 1 else None

        return cls(
            mime_type=mime_type,
            language=language,
            size=size,
            size_bytes=size_bytes,
        )

    def to_string(self) -> str:
        """Serialize this view to a string."""
        parts = [self.mime_type]
        if self.language:
            parts.append(self.language)
        result = " ".join(parts) + ":"
        if self.size:
            result += f" <{self.size}>"
        return result


@dataclass
class AskField:
    """Represents a single field in a Gopher+ ASK block.

    Used for interactive forms/queries.

    Attributes:
        field_type: Type of field (Ask, AskP, AskL, Select, Choose).
        prompt: The prompt text to display.
        default: Default value (if any).
        options: List of options for Select/Choose fields.
    """

    field_type: str
    prompt: str
    default: str | None = None
    options: list[str] = field(default_factory=list)


@dataclass
class GopherAttributes:
    """Gopher+ attribute block.

    Contains metadata about a Gopher+ item including administrative
    information, available views, and descriptions.

    Attributes:
        info: The +INFO line (parsed as GopherItem).
        admin: Administrator name/description.
        admin_email: Administrator email address.
        mod_date: Last modification date.
        creation_date: Creation date.
        views: Available views/representations.
        abstract: Item description/abstract.
        ask_fields: ASK block fields for forms.
        raw: The raw attribute block text.

    Examples:
        >>> attrs = GopherAttributes.parse('''
        ... +INFO: 0About this server\\t/about\\texample.com\\t70
        ... +ADMIN:
        ...  Admin: John Doe <john@example.com>
        ... +ABSTRACT:
        ...  Information about this Gopher server.
        ... ''')
        >>> attrs.abstract
        'Information about this Gopher server.'
    """

    info: GopherItem | None = None
    admin: str | None = None
    admin_email: str | None = None
    mod_date: datetime | None = None
    creation_date: datetime | None = None
    views: list[ViewInfo] = field(default_factory=list)
    abstract: str | None = None
    ask_fields: list[AskField] = field(default_factory=list)
    raw: str = ""

    @classmethod
    def parse(cls, block: str) -> GopherAttributes:
        """Parse a Gopher+ attribute block.

        Args:
            block: The raw attribute block text.

        Returns:
            A GopherAttributes instance.
        """
        # Import here to avoid circular import
        from .response import GopherItem

        attrs = cls(raw=block)

        current_section: str | None = None
        section_lines: list[str] = []

        lines = block.split("\n")

        for line in lines:
            # Check for section headers
            if line.startswith("+"):
                # Process previous section
                if current_section:
                    _process_section(attrs, current_section, section_lines)

                # Start new section
                if line.startswith(ATTR_INFO):
                    current_section = "INFO"
                    # INFO line contains data inline
                    info_data = line[len(ATTR_INFO) :].strip()
                    if info_data:
                        try:
                            attrs.info = GopherItem.from_line(info_data.encode("utf-8"))
                        except ValueError:
                            pass
                    section_lines = []
                elif line.startswith(ATTR_ADMIN):
                    current_section = "ADMIN"
                    section_lines = []
                elif line.startswith(ATTR_VIEWS):
                    current_section = "VIEWS"
                    section_lines = []
                elif line.startswith(ATTR_ABSTRACT):
                    current_section = "ABSTRACT"
                    section_lines = []
                elif line.startswith(ATTR_ASK):
                    current_section = "ASK"
                    section_lines = []
                else:
                    # Unknown section
                    current_section = None
                    section_lines = []
            elif current_section and line.startswith(" "):
                # Continuation line (indented)
                section_lines.append(line[1:])  # Remove leading space

        # Process final section
        if current_section:
            _process_section(attrs, current_section, section_lines)

        return attrs

    def to_string(self) -> str:
        """Serialize this attribute block to a string.

        Returns:
            The attribute block as a string.
        """
        lines: list[str] = []

        if self.info:
            info_line = self.info.to_line().decode("utf-8").rstrip()
            lines.append(f"{ATTR_INFO} {info_line}")

        if self.admin or self.admin_email:
            lines.append(ATTR_ADMIN)
            if self.admin:
                if self.admin_email:
                    lines.append(f" Admin: {self.admin} <{self.admin_email}>")
                else:
                    lines.append(f" Admin: {self.admin}")
            if self.mod_date:
                lines.append(f" Mod-Date: {self.mod_date.isoformat()}")

        if self.views:
            lines.append(ATTR_VIEWS)
            for view in self.views:
                lines.append(f" {view.to_string()}")

        if self.abstract:
            lines.append(ATTR_ABSTRACT)
            for abstract_line in self.abstract.split("\n"):
                lines.append(f" {abstract_line}")

        return "\n".join(lines)


def _process_section(
    attrs: GopherAttributes, section: str, lines: list[str]
) -> None:
    """Process a completed attribute section."""
    if section == "ADMIN":
        _parse_admin(attrs, lines)
    elif section == "VIEWS":
        for line in lines:
            if line.strip():
                attrs.views.append(ViewInfo.parse(line))
    elif section == "ABSTRACT":
        attrs.abstract = "\n".join(lines).strip()
    elif section == "ASK":
        _parse_ask(attrs, lines)


def _parse_admin(attrs: GopherAttributes, lines: list[str]) -> None:
    """Parse ADMIN section lines."""
    for line in lines:
        if line.startswith("Admin:"):
            admin_str = line[6:].strip()
            # Try to extract email from "Name <email>" format
            email_match = re.search(r"<([^>]+)>", admin_str)
            if email_match:
                attrs.admin_email = email_match.group(1)
                attrs.admin = admin_str[: email_match.start()].strip()
            else:
                attrs.admin = admin_str
        elif line.startswith("Mod-Date:"):
            date_str = line[9:].strip()
            try:
                attrs.mod_date = datetime.fromisoformat(date_str)
            except ValueError:
                pass
        elif line.startswith("Creation-Date:"):
            date_str = line[14:].strip()
            try:
                attrs.creation_date = datetime.fromisoformat(date_str)
            except ValueError:
                pass


def _parse_ask(attrs: GopherAttributes, lines: list[str]) -> None:
    """Parse ASK section lines."""
    for line in lines:
        parts = line.split(":", 1)
        if len(parts) == 2:
            field_type = parts[0].strip()
            prompt = parts[1].strip()
            attrs.ask_fields.append(
                AskField(field_type=field_type, prompt=prompt)
            )


def _parse_size(size_str: str) -> int | None:
    """Parse a size string like '10k' or '1.5M' to bytes."""
    size_str = size_str.strip().lower()

    multipliers = {
        "k": 1024,
        "m": 1024 * 1024,
        "g": 1024 * 1024 * 1024,
    }

    for suffix, mult in multipliers.items():
        if size_str.endswith(suffix):
            try:
                return int(float(size_str[:-1]) * mult)
            except ValueError:
                return None

    try:
        return int(size_str)
    except ValueError:
        return None
