from datetime import datetime, timezone
import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider
from fastmcp.server.lifespan import lifespan

from .models import ServerSettings


@lifespan
async def app_lifespan(server):
    logger = logging.getLogger(__name__)
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info("USOS MCP server starting", extra={"started_at": started_at})
    try:
        yield {"started_at": started_at}
    finally:
        logger.info("USOS MCP server stopping")


def create_server() -> FastMCP:
    provider = FileSystemProvider(Path(__file__).parent)
    return FastMCP(
        "USOS MCP server",
        providers=[provider],
        lifespan=app_lifespan,
    )


def main() -> None:
    settings = ServerSettings()
    mcp = create_server()
    kwargs = settings.model_dump()
    if settings.transport == "stdio":
        kwargs.pop("host", None)
        kwargs.pop("port", None)
    mcp.run(**kwargs)