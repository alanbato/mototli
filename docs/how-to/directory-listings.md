# Directory Listings

This guide shows how to customize directory listings in your gopherhole.

## Prerequisites

- Mototli [installed](../installation.md)
- A content directory

## Auto-generated listings

By default, Mototli generates listings automatically when no gophermap exists:

```bash
mkdir my-gopherhole
echo "Hello" > my-gopherhole/hello.txt
mototli serve my-gopherhole --port 7070
```

Visiting the directory shows:

```
[TXT] hello.txt
```

## Create a gophermap

A **gophermap** gives you full control over directory appearance.

Create `gophermap` in your directory:

```
iWelcome to my site!	fake	(NULL)	0
i	fake	(NULL)	0
0Read the welcome message	/hello.txt	localhost	7070
```

### Gophermap format

Each line has this format:

```
TYPE DISPLAY_TEXT <TAB> SELECTOR <TAB> HOST <TAB> PORT
```

| Field | Description |
|-------|-------------|
| Type | Single character item type |
| Display text | Text shown to users |
| Selector | Path to the resource |
| Host | Server hostname |
| Port | Server port |

!!! warning "Tab characters"
    Fields must be separated by **literal tab characters**, not spaces.

## Item types

Common item types:

| Type | Meaning | Example |
|------|---------|---------|
| `i` | Info text (not clickable) | Headers, descriptions |
| `0` | Text file | `.txt` files |
| `1` | Directory | Subdirectories |
| `7` | Search | CGI search scripts |
| `9` | Binary file | Downloads |
| `g` | GIF image | `.gif` files |
| `I` | Other image | `.png`, `.jpg` |
| `h` | HTML link | Web URLs |

See [Item Types Reference](../reference/item-types.md) for the complete list.

## Add informational text

Use type `i` for non-clickable text:

```
i=============================	fake	(NULL)	0
i   Welcome to My Gopherhole	fake	(NULL)	0
i=============================	fake	(NULL)	0
i	fake	(NULL)	0
iThis is my personal gopher site.	fake	(NULL)	0
iUpdated regularly with new content.	fake	(NULL)	0
i	fake	(NULL)	0
```

The `fake`, `(NULL)`, and `0` are placeholders required by the format.

## Link to local files

```
0README	/README.txt	localhost	7070
0Changelog	/CHANGELOG.txt	localhost	7070
1Archive	/archive	localhost	7070
```

## Link to external servers

```
1Floodgap	/	gopher.floodgap.com	70
1SDF Public Access	/	sdf.org	70
```

## Add ASCII art headers

```
i     __  __       _        _   _ _	fake	(NULL)	0
i    |  \/  | ___ | |_ ___ | |_| (_)	fake	(NULL)	0
i    | |\/| |/ _ \| __/ _ \| __| | |	fake	(NULL)	0
i    | |  | | (_) | || (_) | |_| | |	fake	(NULL)	0
i    |_|  |_|\___/ \__\___/ \__|_|_|	fake	(NULL)	0
i	fake	(NULL)	0
```

## Add a search form

```
7Search this site	/cgi-bin/search.py	localhost	7070
```

See [Setup CGI](setup-cgi.md) for implementing the search script.

## Configure default index files

The server looks for index files in this order:

```toml
[handlers]
default_indices = ["gophermap", "index.gph", "index.txt"]
```

First matching file is used.

## Disable auto-generated listings

To require explicit gophermaps:

```toml
[handlers]
enable_directory_listing = false
```

Directories without a gophermap will return an error.

## Add parent directory links

Include a link back to the parent:

```
1..	/	localhost	7070
```

## Complete example

```
i╔═══════════════════════════════════╗	fake	(NULL)	0
i║     Welcome to My Gopherhole      ║	fake	(NULL)	0
i╚═══════════════════════════════════╝	fake	(NULL)	0
i	fake	(NULL)	0
iHello! This is my personal gopher site.	fake	(NULL)	0
iLast updated: January 2025	fake	(NULL)	0
i	fake	(NULL)	0
i--- Navigation ---	fake	(NULL)	0
i	fake	(NULL)	0
0About Me	/about.txt	localhost	7070
1Blog Posts	/blog	localhost	7070
1Projects	/projects	localhost	7070
9Download Archive	/files/archive.tar.gz	localhost	7070
i	fake	(NULL)	0
i--- Search ---	fake	(NULL)	0
i	fake	(NULL)	0
7Search this site	/cgi-bin/search.py	localhost	7070
i	fake	(NULL)	0
i--- External Links ---	fake	(NULL)	0
i	fake	(NULL)	0
1Floodgap Gopher	/	gopher.floodgap.com	70
hWeb Homepage	URL:https://example.com	(NULL)	0
i	fake	(NULL)	0
i---	fake	(NULL)	0
iPowered by Mototli	fake	(NULL)	0
```

## Troubleshooting

### Gophermap not rendering

- Check for **tab characters** between fields (not spaces)
- Verify the file is named exactly `gophermap` (no extension)
- Check file permissions

### Links not working

- Verify the selector path is correct
- Check host and port match your server
- Ensure the target file exists

### Missing items

- Info lines (`i`) require the full format with fake selector
- Each line must have exactly 4 tab-separated fields

## See also

- [:octicons-arrow-right-24: Item Types Reference](../reference/item-types.md) - All item types
- [:octicons-arrow-right-24: Setup CGI](setup-cgi.md) - Dynamic content
- [:octicons-arrow-right-24: Your First Gopherhole](../tutorials/your-first-gopherhole.md) - Complete tutorial
