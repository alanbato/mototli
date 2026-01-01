# Protocol API

API reference for Gopher protocol types.

## ItemType

::: mototli.protocol.ItemType
    options:
      show_root_heading: true
      show_source: true
      members:
        - TEXT
        - DIRECTORY
        - CSO
        - ERROR
        - BINHEX
        - DOS_BINARY
        - UUENCODED
        - SEARCH
        - TELNET
        - BINARY
        - MIRROR
        - GIF
        - IMAGE
        - TN3270
        - INFO
        - HTML
        - SOUND
        - VIDEO
        - DOCUMENT
        - from_char
        - is_text
        - is_binary
        - is_directory
        - is_search
        - is_external
        - is_informational

## GopherRequest

::: mototli.protocol.GopherRequest
    options:
      show_root_heading: true
      show_source: true

## RequestType

::: mototli.protocol.RequestType
    options:
      show_root_heading: true

## GopherResponse

::: mototli.protocol.GopherResponse
    options:
      show_root_heading: true
      show_source: true

## GopherItem

::: mototli.protocol.GopherItem
    options:
      show_root_heading: true
      show_source: true

## GopherAttributes

::: mototli.protocol.GopherAttributes
    options:
      show_root_heading: true
      show_source: true

## ViewInfo

::: mototli.protocol.ViewInfo
    options:
      show_root_heading: true
      show_source: true

## Usage Examples

### Working with ItemType

```python
from mototli.protocol import ItemType

# Parse from character
item_type = ItemType.from_char("0")  # ItemType.TEXT
item_type = ItemType.from_char("1")  # ItemType.DIRECTORY

# Check categories
if item_type.is_text:
    print("This is a text file")
elif item_type.is_binary:
    print("This is a binary file")
elif item_type.is_directory:
    print("This is a directory")

# Get character value
print(item_type.value)  # "0", "1", etc.
```

### Working with GopherRequest

```python
from mototli.protocol import GopherRequest, RequestType

# Parse from wire format
request = GopherRequest.from_line(b"/gopher\r\n")
print(request.selector)      # "/gopher"
print(request.request_type)  # RequestType.NORMAL

# Gopher+ requests
request = GopherRequest.from_line(b"/gopher$\r\n")
print(request.request_type)  # RequestType.ATTRIBUTE_ONLY

# Serialize to wire format
data = request.to_bytes()
```

### Working with GopherResponse

```python
from mototli.protocol import GopherResponse

# Parse directory response
data = b"0Text file\t/file.txt\tlocalhost\t70\r\n.\r\n"
response = GopherResponse.from_bytes(data, is_directory=True)

for item in response.items:
    print(f"[{item.item_type.value}] {item.display_text}")
    print(f"  Selector: {item.selector}")
    print(f"  Host: {item.host}:{item.port}")
```

### Working with GopherItem

```python
from mototli.protocol import GopherItem, ItemType

# Create an item
item = GopherItem(
    item_type=ItemType.TEXT,
    display_text="My Text File",
    selector="/file.txt",
    host="localhost",
    port=70
)

# Serialize to gophermap format
line = item.to_line()
```

### Working with Attributes

```python
from mototli.protocol import GopherAttributes

# Parse attribute block
block = b"+INFO: 0file.txt\t/file.txt\tlocalhost\t70\t+\r\n"
block += b"+ADMIN:\r\n Admin: Name <email>\r\n"
attrs = GopherAttributes.parse(block)

print(attrs.info.display_text)
print(attrs.admin.name)
print(attrs.admin.email)
```

### Helper Functions

```python
from mototli.protocol import create_info_item, create_error_item

# Create info line for gophermap
info = create_info_item("Welcome to my site!")

# Create error response
error = create_error_item("File not found")
```

## Constants

```python
from mototli.protocol import (
    DEFAULT_PORT,      # 70
    CRLF,              # b"\r\n"
    GOPHER_TERMINATOR, # b".\r\n"
)
```

## See Also

- [:octicons-arrow-right-24: Item Types Reference](../item-types.md) - Type codes
- [:octicons-arrow-right-24: Gopher Protocol](../../explanation/gopher-protocol.md) - Protocol overview
- [:octicons-arrow-right-24: Gopher+ Extensions](../../explanation/gopher-plus.md) - Gopher+ details
