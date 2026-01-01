# Gopher Protocol

An introduction to the Gopher protocol, its history, design philosophy, and relevance today.

## A Brief History

Gopher was created at the **University of Minnesota** in 1991, predating the World Wide Web. Named after the university's mascot (and the phrase "go for it"), Gopher was designed to distribute, search, and retrieve documents over the Internet.

### Timeline

| Year | Event |
|------|-------|
| 1991 | Gopher created at University of Minnesota |
| 1992 | RFC 1436 published, standardizing the protocol |
| 1993 | World Wide Web gains popularity |
| 1993 | RFC 4266 (Gopher+) extends the protocol |
| 1993-2000 | Web overtakes Gopher in popularity |
| 2000s | Gopher community continues, smaller but dedicated |
| 2020s | Revival of interest in simple, text-focused protocols |

## Why Gopher Exists

Gopher was designed with specific goals:

### Simplicity

Unlike HTTP, Gopher has minimal overhead:

```
Client sends:    /selector\r\n
Server responds: [content]
```

No headers, no cookies, no JavaScript. Just content.

### Hierarchy

Gopher organizes information in a **menu-based hierarchy**. Each directory listing contains typed links to documents or other directories:

```
1Welcome                /welcome      server.example  70
0FAQ                    /faq.txt      server.example  70
1Archive                /archive      server.example  70
```

This creates a clear, navigable structure.

### Universal Access

Gopher was designed for:

- Low-bandwidth connections
- Text-only terminals
- Consistent rendering across clients

## How Gopher Works

### Request Format

A Gopher request is simply a selector path followed by CRLF:

```
/selector/path\r\n
```

That's it. No HTTP verbs, no headers, no body.

### Response Format

For **text files**, the server sends the content followed by a terminating line:

```
This is the content of the file.
Multiple lines are supported.
.
```

The single period (`.`) on its own line marks the end.

### Directory Listings

Directory listings (menus) have a specific format:

```
TYPE DISPLAY <TAB> SELECTOR <TAB> HOST <TAB> PORT <CRLF>
```

Example:

```
0About this server	/about.txt	gopher.example.com	70
1Document archive	/docs	gopher.example.com	70
iThis is informational text	fake	(NULL)	0
.
```

### Item Types

Each line starts with a type character:

| Type | Meaning |
|------|---------|
| `0` | Text file |
| `1` | Directory (menu) |
| `7` | Search |
| `9` | Binary file |
| `i` | Info text |
| `h` | HTML link |

See [Item Types Reference](../reference/item-types.md) for the complete list.

## Gopher vs. HTTP

| Aspect | Gopher | HTTP |
|--------|--------|------|
| **Complexity** | Minimal | Extensive |
| **Headers** | None | Many |
| **State** | Stateless | Cookies, sessions |
| **Content negotiation** | Gopher+ only | Built-in |
| **Security** | None (plain text) | TLS standard |
| **Rendering** | Server-controlled | Client-controlled |
| **Scripting** | None | JavaScript, etc. |

## Gopher vs. Gemini

Gemini is a modern protocol inspired by Gopher:

| Aspect | Gopher | Gemini |
|--------|--------|--------|
| **Created** | 1991 | 2019 |
| **Encryption** | Optional | Required (TLS) |
| **Line format** | Tab-separated | Space-separated |
| **Item types** | Many | Links only |
| **Protocol** | Plain text | TLS required |

Mototli's sister project [Nauyaca](https://nauyaca.readthedocs.io) implements Gemini.

## Why Gopher in 2025?

Despite its age, Gopher remains relevant:

### Simplicity

In an era of complex web applications, Gopher offers refreshing simplicity. No tracking, no ads, no JavaScript bloat.

### Focus on Content

Gopher enforces a focus on content. Without rich styling, authors must rely on clear writing.

### Low Resource Usage

Gopher servers and clients are lightweight. They work well on minimal hardware and slow connections.

### Digital Minimalism

The "small internet" movement embraces protocols like Gopher as alternatives to the commercial web.

### Educational Value

Gopher is an excellent protocol for learning:

- Simple enough to implement from scratch
- Demonstrates client-server architecture
- Teaches protocol design principles

## The Gopher Community

Active gopher servers ("gopherholes") still exist:

- **Floodgap** - The largest Gopher portal
- **SDF** - Public access Unix system
- **Circumlunar Space** - Gemini/Gopher community

Gopher search engines:

- **Veronica-2** - Full-text Gopher search
- **GopherVR** - 3D Gopher browser

## Mototli's Approach

Mototli implements Gopher with modern Python:

- **Async/await** for efficient networking
- **Type hints** for code quality
- **Gopher+** for enhanced features
- **Rich CLI** for pleasant interaction

We believe Gopher's simplicity deserves modern tooling.

## Further Reading

- [RFC 1436](https://datatracker.ietf.org/doc/html/rfc1436) - The Gopher Protocol
- [RFC 4266](https://datatracker.ietf.org/doc/html/rfc4266) - Gopher+ Extensions
- [Gopher+ Extensions](gopher-plus.md) - Our Gopher+ deep-dive
- [Floodgap Gopher](gopher://gopher.floodgap.com) - The definitive Gopher portal

## See Also

- [:octicons-arrow-right-24: Gopher+ Extensions](gopher-plus.md) - RFC 4266 details
- [:octicons-arrow-right-24: Item Types](../reference/item-types.md) - Type reference
- [:octicons-arrow-right-24: Quick Start](../quickstart.md) - Get started with Mototli
