from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider

from .models import ServerSettings


class USOSMcp:
    def __init__(self,
                 server_settings: ServerSettings | None = None) -> None:
        self.settings = server_settings or ServerSettings()
        provider = FileSystemProvider(Path(__file__).parent)
        self.mcp = FastMCP("USOS MCP server", providers=[provider])

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
