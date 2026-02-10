"""
Minimal HTTP server for platform healthchecks (e.g. Railway).

Responds with 200 OK to GET / so the deployment healthcheck succeeds.
No extra dependencies; uses asyncio only.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

HEALTH_RESPONSE = (
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"Content-Length: 2\r\n"
    b"Connection: close\r\n"
    b"\r\n"
    b"OK"
)


async def _handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Handle one HTTP connection: read request, send 200 for GET / or GET /health."""
    try:
        line = await asyncio.wait_for(reader.readline(), timeout=2.0)
        if line.startswith(b"GET /"):
            writer.write(HEALTH_RESPONSE)
        else:
            writer.write(
                b"HTTP/1.1 404 Not Found\r\n"
                b"Content-Length: 0\r\n"
                b"Connection: close\r\n\r\n"
            )
    except (asyncio.TimeoutError, ConnectionResetError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def run_healthcheck_server(port: int) -> asyncio.Server:
    """
    Start TCP server on given port for healthcheck requests.

    Args:
        port: Port to bind (e.g. from PORT env on Railway).

    Returns:
        Started asyncio.Server (call server.close() and await server.wait_closed() to stop).
    """
    server = await asyncio.start_server(_handle_client, "0.0.0.0", port)
    logger.info("Healthcheck HTTP server listening on port %s", port)
    return server
