"""High-level Gopher client API.

This module provides a high-level async/await interface for making
Gopher requests, built on top of the low-level GopherClientProtocol.
"""

import asyncio

from ..protocol.attributes import GopherAttributes
from ..protocol.constants import DEFAULT_PORT, REQUEST_TIMEOUT
from ..protocol.item_types import ItemType
from ..protocol.request import GopherRequest, RequestType
from ..protocol.response import GopherResponse
from .protocol import GopherClientProtocol, GopherPlusClientProtocol


class GopherClient:
    """High-level Gopher client with async/await API.

    This class provides a simple, high-level interface for getting Gopher
    resources. It handles connection management, timeouts, and response parsing.

    Examples:
        >>> # Basic usage
        >>> async with GopherClient() as client:
        ...     response = await client.get("gopher.floodgap.com")
        ...     for item in response.items:
        ...         print(item)

        >>> # Get a specific resource
        >>> response = await client.get(
        ...     "gopher.floodgap.com",
        ...     selector="/overbite",
        ... )

        >>> # Get with search query
        >>> response = await client.get(
        ...     "gopher.floodgap.com",
        ...     selector="/v2/vs",
        ...     search_query="python",
        ... )
    """

    def __init__(
        self,
        timeout: float = REQUEST_TIMEOUT,
    ):
        """Initialize the Gopher client.

        Args:
            timeout: Request timeout in seconds. Default is 30 seconds.
        """
        self.timeout = timeout

    async def __aenter__(self) -> "GopherClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        pass

    async def get(
        self,
        host: str,
        selector: str = "",
        port: int = DEFAULT_PORT,
        search_query: str | None = None,
        item_type: ItemType = ItemType.DIRECTORY,
    ) -> GopherResponse:
        """Get a Gopher resource.

        Args:
            host: The Gopher server hostname.
            selector: The resource selector (path). Default is empty (root).
            port: The server port. Default is 70.
            search_query: Optional search query for type 7 (search) items.
            item_type: Expected item type. Used to determine if response is a
                directory listing. Default is DIRECTORY.

        Returns:
            A GopherResponse object with items (for directories) or raw_body.

        Raises:
            asyncio.TimeoutError: If the request times out.
            ConnectionError: If the connection fails.

        Examples:
            >>> response = await client.get("gopher.floodgap.com")
            >>> for item in response.items:
            ...     print(f"[{item.item_type.value}] {item.display_text}")
        """
        request = GopherRequest(
            selector=selector,
            search_query=search_query,
        )

        is_directory = item_type.is_directory or item_type == ItemType.SEARCH

        return await self._send_request(
            host=host,
            port=port,
            request=request,
            is_directory=is_directory,
        )

    async def get_text(
        self,
        host: str,
        selector: str,
        port: int = DEFAULT_PORT,
    ) -> str:
        """Get a text resource and return its content as a string.

        Args:
            host: The Gopher server hostname.
            selector: The resource selector (path).
            port: The server port. Default is 70.

        Returns:
            The text content as a string.

        Raises:
            asyncio.TimeoutError: If the request times out.
            ConnectionError: If the connection fails.
            ValueError: If the response is not text.

        Examples:
            >>> text = await client.get_text(
            ...     "gopher.floodgap.com",
            ...     "/gopher/welcome",
            ... )
            >>> print(text)
        """
        response = await self.get(
            host=host,
            selector=selector,
            port=port,
            item_type=ItemType.TEXT,
        )

        if response.text is None:
            raise ValueError("Response is not text content")

        return response.text

    async def get_binary(
        self,
        host: str,
        selector: str,
        port: int = DEFAULT_PORT,
    ) -> bytes:
        """Get a binary resource.

        Args:
            host: The Gopher server hostname.
            selector: The resource selector (path).
            port: The server port. Default is 70.

        Returns:
            The binary content as bytes.

        Raises:
            asyncio.TimeoutError: If the request times out.
            ConnectionError: If the connection fails.

        Examples:
            >>> data = await client.get_binary(
            ...     "gopher.floodgap.com",
            ...     "/some/image.gif",
            ... )
            >>> with open("image.gif", "wb") as f:
            ...     f.write(data)
        """
        response = await self.get(
            host=host,
            selector=selector,
            port=port,
            item_type=ItemType.BINARY,
        )

        return response.raw_body or b""

    async def get_attributes(
        self,
        host: str,
        selector: str,
        port: int = DEFAULT_PORT,
    ) -> GopherAttributes:
        """Get Gopher+ attributes for a resource.

        Args:
            host: The Gopher server hostname.
            selector: The resource selector (path).
            port: The server port. Default is 70.

        Returns:
            A GopherAttributes object with metadata.

        Raises:
            asyncio.TimeoutError: If the request times out.
            ConnectionError: If the connection fails.

        Examples:
            >>> attrs = await client.get_attributes(
            ...     "gopher.example.com",
            ...     "/about",
            ... )
            >>> print(attrs.abstract)
        """
        request = GopherRequest(
            selector=selector,
            request_type=RequestType.ATTRIBUTES,
        )

        raw_bytes = await self._send_raw_request(
            host=host,
            port=port,
            request=request,
            is_directory=False,
            use_gopher_plus=True,
        )

        return GopherAttributes.parse(raw_bytes.decode("utf-8", errors="replace"))

    async def get_with_view(
        self,
        host: str,
        selector: str,
        view_type: str,
        port: int = DEFAULT_PORT,
    ) -> GopherResponse:
        """Get a specific view of a Gopher+ resource.

        Args:
            host: The Gopher server hostname.
            selector: The resource selector (path).
            view_type: The MIME type of the view to request.
            port: The server port. Default is 70.

        Returns:
            A GopherResponse with the requested view.

        Raises:
            asyncio.TimeoutError: If the request times out.
            ConnectionError: If the connection fails.

        Examples:
            >>> response = await client.get_with_view(
            ...     "gopher.example.com",
            ...     "/document",
            ...     "text/plain",
            ... )
        """
        request = GopherRequest(
            selector=selector,
            request_type=RequestType.PLUS,
            view_type=view_type,
        )

        return await self._send_request(
            host=host,
            port=port,
            request=request,
            is_directory=False,
        )

    async def _send_request(
        self,
        host: str,
        port: int,
        request: GopherRequest,
        is_directory: bool,
    ) -> GopherResponse:
        """Send a request and parse the response.

        Args:
            host: The server hostname.
            port: The server port.
            request: The request to send.
            is_directory: Whether to parse response as directory listing.

        Returns:
            A parsed GopherResponse.
        """
        raw_bytes = await self._send_raw_request(
            host=host,
            port=port,
            request=request,
            is_directory=is_directory,
        )

        return GopherResponse.from_bytes(raw_bytes, is_directory=is_directory)

    async def _send_raw_request(
        self,
        host: str,
        port: int,
        request: GopherRequest,
        is_directory: bool,
        use_gopher_plus: bool = False,
    ) -> bytes:
        """Send a request and return raw response bytes.

        Args:
            host: The server hostname.
            port: The server port.
            request: The request to send.
            is_directory: Whether this is a directory request.
            use_gopher_plus: Whether to use Gopher+ protocol handling.

        Returns:
            Raw response bytes.
        """
        loop = asyncio.get_running_loop()

        # Create future for response
        response_future: asyncio.Future[bytes] = loop.create_future()

        # Create protocol instance
        if use_gopher_plus or request.is_gopher_plus:
            protocol = GopherPlusClientProtocol(
                request=request,
                response_future=response_future,
                is_directory=is_directory,
            )
        else:
            protocol = GopherClientProtocol(
                request=request,
                response_future=response_future,
                is_directory=is_directory,
            )

        # Create connection
        try:
            transport, _ = await asyncio.wait_for(
                loop.create_connection(
                    lambda: protocol,
                    host=host,
                    port=port,
                ),
                timeout=self.timeout,
            )
        except TimeoutError as e:
            raise TimeoutError(f"Connection timeout: {host}:{port}") from e
        except OSError as e:
            raise ConnectionError(f"Connection failed: {e}") from e

        try:
            # Wait for response with timeout
            response_bytes: bytes = await asyncio.wait_for(
                response_future, timeout=self.timeout
            )
            return response_bytes
        except TimeoutError as e:
            raise TimeoutError(
                f"Request timeout: {host}:{port}{request.selector}"
            ) from e
        finally:
            # Ensure transport is closed
            transport.close()
