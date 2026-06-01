from datetime import datetime, timezone
import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider
from fastmcp.server.lifespan import lifespan

from .models import ServerSettings


class USOSMcp:
    def __init__(self,
                 server_settings: ServerSettings | None = None) -> None:
        self.settings = server_settings or ServerSettings()
        provider = FileSystemProvider(Path(__file__).parent)
        self.mcp = FastMCP(
            "USOS MCP server",
            providers=[provider],
            lifespan=app_lifespan,
        )

    @property
    def server(self):
        return self.mcp.server

    def run(self) -> None:
        kwargs = self.settings.model_dump()
        if self.settings.transport == "stdio":
            kwargs.pop("host", None)
            kwargs.pop("port", None)
        self.mcp.run(**kwargs)

# Used for fastmcp.json
def get_mcp() -> FastMCP:
    return USOSMcp().mcp


# Main entrypoint
def main() -> None:
    app = USOSMcp()
    app.run()


@lifespan
async def app_lifespan(server):
    logger = logging.getLogger(__name__)
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info("USOS MCP server starting", extra={"started_at": started_at})
    try:
        yield {"started_at": started_at}
    finally:
        logger.info("USOS MCP server stopping")
