"""Tests for Gopher item types."""

import pytest

from mototli.protocol.item_types import ItemType


class TestItemTypeValues:
    """Tests for item type character values."""

    def test_text_type(self):
        """Text file type should be '0'."""
        assert ItemType.TEXT.value == "0"

    def test_directory_type(self):
        """Directory type should be '1'."""
        assert ItemType.DIRECTORY.value == "1"

    def test_cso_type(self):
        """CSO phonebook type should be '2'."""
        assert ItemType.CSO.value == "2"

    def test_error_type(self):
        """Error type should be '3'."""
        assert ItemType.ERROR.value == "3"

    def test_binhex_type(self):
        """BinHex type should be '4'."""
        assert ItemType.BINHEX.value == "4"

    def test_dos_binary_type(self):
        """DOS binary type should be '5'."""
        assert ItemType.DOS_BINARY.value == "5"

    def test_uuencoded_type(self):
        """UUencoded type should be '6'."""
        assert ItemType.UUENCODED.value == "6"

    def test_search_type(self):
        """Search type should be '7'."""
        assert ItemType.SEARCH.value == "7"

    def test_telnet_type(self):
        """Telnet type should be '8'."""
        assert ItemType.TELNET.value == "8"

    def test_binary_type(self):
        """Binary type should be '9'."""
        assert ItemType.BINARY.value == "9"

    def test_mirror_type(self):
        """Mirror type should be '+'."""
        assert ItemType.MIRROR.value == "+"

    def test_gif_type(self):
        """GIF type should be 'g'."""
        assert ItemType.GIF.value == "g"

    def test_image_type(self):
        """Image type should be 'I'."""
        assert ItemType.IMAGE.value == "I"

    def test_tn3270_type(self):
        """TN3270 type should be 'T'."""
        assert ItemType.TN3270.value == "T"

    def test_html_type(self):
        """HTML type should be 'h'."""
        assert ItemType.HTML.value == "h"

    def test_info_type(self):
        """Info type should be 'i'."""
        assert ItemType.INFO.value == "i"

    def test_audio_type(self):
        """Audio type should be 's'."""
        assert ItemType.AUDIO.value == "s"


class TestFromChar:
    """Tests for ItemType.from_char() method."""

    def test_from_char_text(self):
        """Should parse text type from '0'."""
        assert ItemType.from_char("0") == ItemType.TEXT

    def test_from_char_directory(self):
        """Should parse directory type from '1'."""
        assert ItemType.from_char("1") == ItemType.DIRECTORY

    def test_from_char_search(self):
        """Should parse search type from '7'."""
        assert ItemType.from_char("7") == ItemType.SEARCH

    def test_from_char_info(self):
        """Should parse info type from 'i'."""
        assert ItemType.from_char("i") == ItemType.INFO

    def test_from_char_html(self):
        """Should parse HTML type from 'h'."""
        assert ItemType.from_char("h") == ItemType.HTML

    def test_from_char_unknown_raises(self):
        """Should raise ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown item type"):
            ItemType.from_char("x")

    def test_from_char_empty_raises(self):
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError):
            ItemType.from_char("")

    @pytest.mark.parametrize(
        "char,expected",
        [
            ("0", ItemType.TEXT),
            ("1", ItemType.DIRECTORY),
            ("2", ItemType.CSO),
            ("3", ItemType.ERROR),
            ("7", ItemType.SEARCH),
            ("9", ItemType.BINARY),
            ("g", ItemType.GIF),
            ("I", ItemType.IMAGE),
            ("i", ItemType.INFO),
            ("h", ItemType.HTML),
            ("s", ItemType.AUDIO),
        ],
    )
    def test_from_char_all_types(self, char, expected):
        """Should correctly parse all item types."""
        assert ItemType.from_char(char) == expected


class TestIsDirectory:
    """Tests for is_directory property."""

    def test_directory_is_directory(self):
        """Directory type should be a directory."""
        assert ItemType.DIRECTORY.is_directory is True

    def test_text_is_not_directory(self):
        """Text type should not be a directory."""
        assert ItemType.TEXT.is_directory is False

    def test_search_is_not_directory(self):
        """Search type should not be a directory."""
        assert ItemType.SEARCH.is_directory is False


class TestIsSearch:
    """Tests for is_search property."""

    def test_search_is_search(self):
        """Search type should be a search."""
        assert ItemType.SEARCH.is_search is True

    def test_directory_is_not_search(self):
        """Directory type should not be a search."""
        assert ItemType.DIRECTORY.is_search is False

    def test_text_is_not_search(self):
        """Text type should not be a search."""
        assert ItemType.TEXT.is_search is False


class TestIsBinary:
    """Tests for is_binary property."""

    def test_binary_is_binary(self):
        """Binary type should be binary."""
        assert ItemType.BINARY.is_binary is True

    def test_gif_is_binary(self):
        """GIF type should be binary."""
        assert ItemType.GIF.is_binary is True

    def test_image_is_binary(self):
        """Image type should be binary."""
        assert ItemType.IMAGE.is_binary is True

    def test_audio_is_binary(self):
        """Audio type should be binary."""
        assert ItemType.AUDIO.is_binary is True

    def test_dos_binary_is_binary(self):
        """DOS binary type should be binary."""
        assert ItemType.DOS_BINARY.is_binary is True

    def test_text_is_not_binary(self):
        """Text type should not be binary."""
        assert ItemType.TEXT.is_binary is False

    def test_directory_is_not_binary(self):
        """Directory type should not be binary."""
        assert ItemType.DIRECTORY.is_binary is False


class TestIsText:
    """Tests for is_text property."""

    def test_text_is_text(self):
        """Text type should be text."""
        assert ItemType.TEXT.is_text is True

    def test_html_is_text(self):
        """HTML type should be text."""
        assert ItemType.HTML.is_text is True

    def test_doc_is_text(self):
        """Doc type should be text."""
        assert ItemType.DOC.is_text is True

    def test_binary_is_not_text(self):
        """Binary type should not be text."""
        assert ItemType.BINARY.is_text is False

    def test_directory_is_not_text(self):
        """Directory type should not be text."""
        assert ItemType.DIRECTORY.is_text is False


class TestIsInformational:
    """Tests for is_informational property."""

    def test_info_is_informational(self):
        """Info type should be informational."""
        assert ItemType.INFO.is_informational is True

    def test_error_is_informational(self):
        """Error type should be informational."""
        assert ItemType.ERROR.is_informational is True

    def test_text_is_not_informational(self):
        """Text type should not be informational."""
        assert ItemType.TEXT.is_informational is False

    def test_directory_is_not_informational(self):
        """Directory type should not be informational."""
        assert ItemType.DIRECTORY.is_informational is False


class TestIsExternal:
    """Tests for is_external property."""

    def test_telnet_is_external(self):
        """Telnet type should be external."""
        assert ItemType.TELNET.is_external is True

    def test_tn3270_is_external(self):
        """TN3270 type should be external."""
        assert ItemType.TN3270.is_external is True

    def test_text_is_not_external(self):
        """Text type should not be external."""
        assert ItemType.TEXT.is_external is False

    def test_directory_is_not_external(self):
        """Directory type should not be external."""
        assert ItemType.DIRECTORY.is_external is False


class TestStringEnum:
    """Tests for string enum behavior."""

    def test_item_type_is_str(self):
        """ItemType should be usable as a string."""
        assert ItemType.TEXT == "0"
        assert ItemType.DIRECTORY == "1"

    def test_item_type_concatenation(self):
        """ItemType should be concatenable with strings."""
        result = ItemType.TEXT + "Hello"
        assert result == "0Hello"
