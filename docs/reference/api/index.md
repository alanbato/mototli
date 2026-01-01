# API Reference

Python API documentation for Mototli modules.

<div class="grid cards" markdown>

-   :material-download: **Client**

    ---

    `GopherClient` for fetching resources from gopher servers.

    [:octicons-arrow-right-24: Client API](client.md)

-   :material-server: **Server**

    ---

    `GopherServer`, `ServerConfig`, and handler classes.

    [:octicons-arrow-right-24: Server API](server.md)

-   :material-code-braces: **Protocol**

    ---

    Protocol types: `ItemType`, `GopherRequest`, `GopherResponse`.

    [:octicons-arrow-right-24: Protocol API](protocol.md)

</div>

## Module Overview

```
mototli
├── client          # Client implementation
│   ├── GopherClient
│   └── GopherClientProtocol
├── server          # Server implementation
│   ├── GopherServer
│   ├── ServerConfig
│   ├── Router
│   └── handlers
├── protocol        # Protocol types
│   ├── ItemType
│   ├── GopherRequest
│   ├── GopherResponse
│   └── GopherAttributes
├── content         # Content generation
│   └── directory
└── utils           # Utilities
    └── mime
```

## Quick Import Reference

```python
# Client
from mototli.client import GopherClient

# Server
from mototli.server import (
    GopherServer,
    ServerConfig,
    run_server,
    start_server,
)

# Protocol types
from mototli.protocol import (
    ItemType,
    GopherRequest,
    GopherResponse,
    GopherItem,
    GopherAttributes,
)

# Utilities
from mototli.utils import get_item_type, get_mime_type
```

## See Also

- [:octicons-arrow-right-24: Building a Client](../../tutorials/building-a-client.md) - Client tutorial
- [:octicons-arrow-right-24: Your First Gopherhole](../../tutorials/your-first-gopherhole.md) - Server tutorial
