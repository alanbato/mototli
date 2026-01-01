# Gopher+ Extensions

A deep dive into Gopher+ (RFC 4266), which extends the original Gopher protocol with metadata, alternate views, and enhanced capabilities.

## What is Gopher+?

Gopher+ was developed to address limitations in the original Gopher protocol:

- No way to know file sizes before downloading
- No metadata about content (author, date, type)
- No content negotiation
- No way to provide alternate formats

Gopher+ adds these features while remaining backwards-compatible with classic Gopher.

## Request Modifiers

Gopher+ introduces special characters appended to selectors:

### The `$` Modifier (Attributes Only)

Request metadata without downloading content:

```
/large-file.zip$\r\n
```

Response contains attribute blocks, not the file itself. Useful for:

- Checking file size before download
- Getting content type information
- Viewing available alternate formats

### The `+` Modifier (View Request)

Request a specific content representation:

```
/document+text/plain\r\n
```

Server returns the document in the requested format if available.

### The `!` Modifier (Full Request)

Request content with attributes prepended:

```
/file.txt!\r\n
```

Response includes both attributes and content.

## Attribute Blocks

Gopher+ responses include structured metadata:

### +INFO

Basic item information (same as directory line):

```
+INFO: 0document.txt	/document.txt	server.example	70	+
```

The trailing `+` indicates Gopher+ support.

### +ADMIN

Server administrator information:

```
+ADMIN:
 Admin: Site Admin <admin@example.com>
 Mod-Date: <20240115120000>
```

Fields:
- **Admin**: Name and email of administrator
- **Mod-Date**: Last modification date (YYYYMMDDhhmmss format)

### +VIEWS

Available content representations:

```
+VIEWS:
 text/plain: <15k>
 text/html: <25k>
 application/pdf: <150k>
```

Each view shows:
- MIME content type
- Approximate size in angle brackets

### +ABSTRACT

Short description of the item:

```
+ABSTRACT:
 This document explains the Gopher+ protocol extensions
 and how to use them effectively.
```

### +ASK

Interactive form elements (rarely implemented):

```
+ASK:
 Ask: What is your name?
 Choose: Preferred format	text	html	pdf
```

## Directory Listing Format

Gopher+ directory entries include a Gopher+ indicator:

```
0Document	/doc.txt	server.example	70	+
1Archive	/archive	server.example	70	+
```

The `+` after the port indicates the item supports Gopher+ queries.

## Compatibility

### With Classic Gopher

Gopher+ is backwards-compatible:

1. Classic clients send: `/selector\r\n`
2. Server responds with classic Gopher format
3. Client never sees Gopher+ features

### Detecting Support

Check for the `+` flag in directory listings:

```python
for item in response.items:
    if item.gopher_plus:
        # Item supports Gopher+ queries
        attrs = await client.get_attributes(item.host, item.selector)
```

## Use Cases

### Preview Before Download

```python
# Check size before downloading a large file
attrs = await client.get_attributes(host, "/large-archive.zip")
if attrs.info and attrs.info.size > 100_000_000:
    print("Warning: File is over 100MB")
    if not confirm():
        return
response = await client.get_binary(host, "/large-archive.zip")
```

### Content Negotiation

```python
# Get available formats
attrs = await client.get_attributes(host, "/document")

# Find preferred format
for view in attrs.views:
    if view.content_type == "text/plain":
        response = await client.get_with_view(host, "/document", "text/plain")
        break
```

### Administrative Contact

```python
# Get site admin info
attrs = await client.get_attributes(host, "/")

if attrs.admin:
    print(f"Contact: {attrs.admin.name}")
    print(f"Email: {attrs.admin.email}")
```

## Implementation in Mototli

### Server Support

Mototli servers have Gopher+ enabled by default:

```toml
[gopher_plus]
enabled = true
admin_name = "Your Name"
admin_email = "you@example.com"
```

### Client Support

The `GopherClient` provides Gopher+ methods:

```python
# Get attributes
attrs = await client.get_attributes(host, selector)

# Request specific view
response = await client.get_with_view(host, selector, "text/plain")
```

### CLI Support

Query attributes from the command line:

```bash
mototli attrs gopher.floodgap.com /gopher
```

## Practical Considerations

### Not All Servers Support Gopher+

Always handle the case where Gopher+ is unavailable:

```python
try:
    attrs = await client.get_attributes(host, selector)
except Exception:
    # Fall back to regular fetch
    response = await client.get(host, selector)
```

### Size Information May Be Approximate

The `<15k>` notation indicates approximate size. Don't rely on it for exact byte counts.

### Views May Not Be Available

A server might support Gopher+ but not have alternate views for every document.

## Protocol Details

### Request Formats

| Request | Meaning |
|---------|---------|
| `/selector\r\n` | Classic Gopher |
| `/selector$\r\n` | Attributes only |
| `/selector+view\r\n` | Specific view |
| `/selector!\r\n` | Content with attributes |

### Response Status

Gopher+ responses begin with status:

| Status | Meaning |
|--------|---------|
| `+` | Success, content follows |
| `-` | Success, content follows (legacy) |
| `--1\r\n` | Item doesn't exist |
| `--2\r\n` | Access denied |

## Further Reading

- [RFC 4266](https://datatracker.ietf.org/doc/html/rfc4266) - The Gopher+ Specification
- [Understanding Gopher+](../tutorials/understanding-gopher-plus.md) - Hands-on tutorial
- [Protocol API](../reference/api/protocol.md) - Attribute classes

## See Also

- [:octicons-arrow-right-24: Gopher Protocol](gopher-protocol.md) - Protocol basics
- [:octicons-arrow-right-24: Understanding Gopher+](../tutorials/understanding-gopher-plus.md) - Tutorial
- [:octicons-arrow-right-24: Client API](../reference/api/client.md) - Client methods
