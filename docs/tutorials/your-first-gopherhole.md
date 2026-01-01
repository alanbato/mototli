# Your First Gopherhole

In this tutorial, you'll create and serve your first gopher site (called a "gopherhole"). You'll learn how to:

- Set up a directory structure for gopher content
- Write text files and gophermaps
- Start and configure the Mototli server
- Browse your site with the client

**Difficulty**: Beginner
**Time**: ~15 minutes
**Prerequisites**: Mototli [installed](../installation.md)

---

## Step 1: Create the directory structure

Create a directory for your gopherhole:

```bash
mkdir -p my-gopherhole/about
cd my-gopherhole
```

Your structure will look like:

```
my-gopherhole/
├── gophermap      # Directory listing (we'll create this)
├── welcome.txt    # A text file
└── about/
    └── me.txt     # Another text file
```

---

## Step 2: Create a welcome file

Create `welcome.txt` with your welcome message:

```bash
cat > welcome.txt << 'EOF'
Welcome to My Gopherhole!
==========================

This is a simple gopher site served by Mototli.

Gopher is a protocol from the early 1990s that provides
a simple, text-based way to share information.

Thanks for visiting!
EOF
```

---

## Step 3: Create an about page

Create `about/me.txt`:

```bash
cat > about/me.txt << 'EOF'
About Me
========

I'm learning about the Gopher protocol using Mototli.

Gopher was created at the University of Minnesota in 1991
and predates the World Wide Web. It offers a simpler,
more focused browsing experience.
EOF
```

---

## Step 4: Create a gophermap

A **gophermap** is a special file that defines how your directory appears to visitors. Create `gophermap`:

```bash
cat > gophermap << 'EOF'
i     __  __       _        _   _ _ 	fake	(NULL)	0
i    |  \/  | ___ | |_ ___ | |_| (_)	fake	(NULL)	0
i    | |\/| |/ _ \| __/ _ \| __| | |	fake	(NULL)	0
i    | |  | | (_) | || (_) | |_| | |	fake	(NULL)	0
i    |_|  |_|\___/ \__\___/ \__|_|_|	fake	(NULL)	0
i	fake	(NULL)	0
iWelcome to my gopherhole!	fake	(NULL)	0
i	fake	(NULL)	0
0Read the welcome message	/welcome.txt	localhost	7070
1About section	/about	localhost	7070
i	fake	(NULL)	0
i---	fake	(NULL)	0
iPowered by Mototli	fake	(NULL)	0
EOF
```

### Gophermap Format

Each line follows this format:

```
TYPE DISPLAY_TEXT <TAB> SELECTOR <TAB> HOST <TAB> PORT
```

| Type | Meaning |
|------|---------|
| `i` | Informational text (not a link) |
| `0` | Text file |
| `1` | Directory |
| `9` | Binary file |
| `g` | GIF image |
| `I` | Other image |

!!! tip "Tab characters"
    The separator between fields must be a literal tab character, not spaces.

---

## Step 5: Start the server

Start Mototli serving your content:

```bash
mototli serve . --port 7070 --hostname localhost
```

You'll see:

```
Starting Gopher server...
  Document root: /path/to/my-gopherhole
  Listening on: localhost:7070
  Gopher+ enabled: Yes

Press Ctrl+C to stop
```

!!! note "Port 70"
    The standard Gopher port is 70, but it requires root privileges.
    Use port 7070 for development.

---

## Step 6: Browse your site

Open another terminal and browse your gopherhole:

```bash
mototli get localhost:7070
```

You should see your gophermap rendered:

```
     __  __       _        _   _ _
    |  \/  | ___ | |_ ___ | |_| (_)
    | |\/| |/ _ \| __/ _ \| __| | |
    | |  | | (_) | || (_) | |_| | |
    |_|  |_|\___/ \__\___/ \__|_|_|

Welcome to my gopherhole!

[TXT] Read the welcome message
[DIR] About section

---
Powered by Mototli
```

Fetch a text file:

```bash
mototli text localhost:7070 /welcome.txt
```

Browse a subdirectory:

```bash
mototli get localhost:7070 /about
```

---

## Step 7: Add more content

Let's add a binary file. Create a simple text art image:

```bash
cat > logo.txt << 'EOF'
    .--.
   |o_o |
   |:_/ |
  //   \ \
 (|     | )
/'\_   _/`\
\___)=(___/
EOF
```

Update your gophermap to include it:

```bash
cat > gophermap << 'EOF'
i     __  __       _        _   _ _ 	fake	(NULL)	0
i    |  \/  | ___ | |_ ___ | |_| (_)	fake	(NULL)	0
i    | |\/| |/ _ \| __/ _ \| __| | |	fake	(NULL)	0
i    | |  | | (_) | || (_) | |_| | |	fake	(NULL)	0
i    |_|  |_|\___/ \__\___/ \__|_|_|	fake	(NULL)	0
i	fake	(NULL)	0
iWelcome to my gopherhole!	fake	(NULL)	0
i	fake	(NULL)	0
0Read the welcome message	/welcome.txt	localhost	7070
0View the penguin logo	/logo.txt	localhost	7070
1About section	/about	localhost	7070
i	fake	(NULL)	0
i---	fake	(NULL)	0
iPowered by Mototli	fake	(NULL)	0
EOF
```

Refresh your client view to see the new link.

---

## Step 8: Use auto-generated listings

If you don't provide a gophermap, Mototli generates one automatically. Delete your gophermap:

```bash
rm gophermap
```

Now browse again:

```bash
mototli get localhost:7070
```

You'll see an auto-generated listing of your files.

---

## Summary

You've learned how to:

- [x] Create a directory structure for gopher content
- [x] Write text files served via Gopher
- [x] Create gophermaps for custom directory listings
- [x] Start the Mototli server
- [x] Browse content with the CLI client
- [x] Use auto-generated directory listings

---

## Common Issues

### "Connection refused"

The server isn't running. Make sure you started it with:

```bash
mototli serve . --port 7070
```

### Gophermap not rendering correctly

- Ensure you're using **tab characters** between fields, not spaces
- Check that the port in your gophermap matches your server port

### Can't access port 70

Port 70 requires root privileges. Use a higher port for development:

```bash
mototli serve . --port 7070
```

---

## Next Steps

- [:octicons-arrow-right-24: Building a Client](building-a-client.md) - Access gopher programmatically
- [:octicons-arrow-right-24: Configure Server](../how-to/configure-server.md) - Advanced server configuration
- [:octicons-arrow-right-24: Setup CGI](../how-to/setup-cgi.md) - Add dynamic content
