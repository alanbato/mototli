# Item Types Reference

Complete reference for Gopher item types as defined in RFC 1436 and common extensions.

## Overview

Gopher uses single-character codes to identify item types. These appear as the first character of each line in a directory listing.

## Core Types (RFC 1436)

| Code | Name | Constant | Description |
|------|------|----------|-------------|
| `0` | Text | `ItemType.TEXT` | Plain text file |
| `1` | Directory | `ItemType.DIRECTORY` | Gopher menu/directory |
| `2` | CSO | `ItemType.CSO` | CSO phone-book server |
| `3` | Error | `ItemType.ERROR` | Error message |
| `4` | BinHex | `ItemType.BINHEX` | BinHex-encoded file |
| `5` | DOS | `ItemType.DOS_BINARY` | DOS binary archive |
| `6` | UUEncoded | `ItemType.UUENCODED` | UUEncoded text |
| `7` | Search | `ItemType.SEARCH` | Full-text search |
| `8` | Telnet | `ItemType.TELNET` | Telnet session |
| `9` | Binary | `ItemType.BINARY` | Binary file |
| `+` | Mirror | `ItemType.MIRROR` | Redundant server |
| `g` | GIF | `ItemType.GIF` | GIF image |
| `I` | Image | `ItemType.IMAGE` | Other image format |
| `T` | TN3270 | `ItemType.TN3270` | TN3270 session |

## Extended Types

Common extensions beyond RFC 1436:

| Code | Name | Constant | Description |
|------|------|----------|-------------|
| `i` | Info | `ItemType.INFO` | Informational text (not selectable) |
| `h` | HTML | `ItemType.HTML` | HTML document or URL |
| `s` | Sound | `ItemType.SOUND` | Audio file |
| `d` | Document | `ItemType.DOCUMENT` | PDF or other document |
| `;` | Video | `ItemType.VIDEO` | Video file |
| `c` | Calendar | `ItemType.CALENDAR` | Calendar data |
| `M` | MIME | `ItemType.MIME` | MIME-encoded data |
| `P` | PDF | `ItemType.PDF` | PDF document |

## Type Categories

### Text Types

Types that contain readable text:

```python
from mototli.protocol import ItemType

text_types = [
    ItemType.TEXT,       # 0 - Plain text
    ItemType.INFO,       # i - Info line
    ItemType.ERROR,      # 3 - Error message
]

# Check if type is text
if item_type.is_text:
    # Decode as text
    content = response.content.decode()
```

### Binary Types

Types that contain binary data:

```python
binary_types = [
    ItemType.BINARY,      # 9 - Generic binary
    ItemType.DOS_BINARY,  # 5 - DOS binary
    ItemType.GIF,         # g - GIF image
    ItemType.IMAGE,       # I - Other image
    ItemType.SOUND,       # s - Audio
    ItemType.VIDEO,       # ; - Video
    ItemType.PDF,         # P - PDF
]

# Check if type is binary
if item_type.is_binary:
    # Handle as bytes
    with open("file", "wb") as f:
        f.write(response.content)
```

### Directory Types

Types that represent navigable directories:

```python
directory_types = [
    ItemType.DIRECTORY,  # 1 - Standard directory
    ItemType.SEARCH,     # 7 - Search (returns directory)
]

# Check if type is directory
if item_type.is_directory:
    for item in response.items:
        print(item.display_text)
```

### External Types

Types that require external handling:

```python
external_types = [
    ItemType.TELNET,   # 8 - Telnet session
    ItemType.TN3270,   # T - TN3270 session
    ItemType.HTML,     # h - HTML/web link
]

# Check if type is external
if item_type.is_external:
    print(f"External resource: {item.selector}")
```

### Informational Types

Types that are display-only (not selectable):

```python
info_types = [
    ItemType.INFO,   # i - Info text
]

# Check if informational
if item_type.is_informational:
    # Don't create a link
    print(f"  {item.display_text}")
```

## ItemType Properties

The `ItemType` enum provides convenience properties:

```python
from mototli.protocol import ItemType

item_type = ItemType.TEXT

# Category checks
item_type.is_text          # True for text files
item_type.is_binary        # True for binary files
item_type.is_directory     # True for directories
item_type.is_search        # True for search items
item_type.is_external      # True for telnet, HTML
item_type.is_informational # True for info lines

# Get character code
item_type.value  # "0"
```

## Parsing Item Types

```python
from mototli.protocol import ItemType

# From character
item_type = ItemType.from_char("0")  # ItemType.TEXT
item_type = ItemType.from_char("1")  # ItemType.DIRECTORY
item_type = ItemType.from_char("i")  # ItemType.INFO

# Unknown types return BINARY
item_type = ItemType.from_char("?")  # ItemType.BINARY
```

## MIME Type Mapping

Mototli maps file extensions to item types:

| Extension | MIME Type | Item Type |
|-----------|-----------|-----------|
| `.txt`, `.md` | text/plain | TEXT |
| `.html`, `.htm` | text/html | HTML |
| `.gif` | image/gif | GIF |
| `.png`, `.jpg`, `.jpeg` | image/* | IMAGE |
| `.mp3`, `.wav`, `.ogg` | audio/* | SOUND |
| `.mp4`, `.avi`, `.mkv` | video/* | VIDEO |
| `.pdf` | application/pdf | PDF |
| `.tar`, `.zip`, `.gz` | application/* | BINARY |

```python
from mototli.utils import get_item_type
from pathlib import Path

# Get item type from file
item_type = get_item_type(Path("image.png"))  # ItemType.IMAGE
item_type = get_item_type(Path("doc.pdf"))    # ItemType.PDF
```

## Gophermap Examples

```
iThis is an info line	fake	(NULL)	0
0Text file	/file.txt	localhost	70
1Subdirectory	/subdir	localhost	70
7Search	/search	localhost	70
9Binary download	/file.zip	localhost	70
gGIF image	/image.gif	localhost	70
IPhoto	/photo.jpg	localhost	70
hWeb link	URL:https://example.com	(NULL)	0
```

## See Also

- [:octicons-arrow-right-24: Directory Listings](../how-to/directory-listings.md) - Using types in gophermaps
- [:octicons-arrow-right-24: Protocol API](api/protocol.md) - ItemType enum
- [:octicons-arrow-right-24: Gopher Protocol](../explanation/gopher-protocol.md) - Protocol overview
