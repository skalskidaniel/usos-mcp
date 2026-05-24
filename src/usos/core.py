from fastmcp import FastMCP
import importlib
import pkgutil

from .models import ServerSettings
from .registry import registry
import usos


def discover_modules():
    """Dynamically imports all tools.py and prompts.py across the usos package."""
    package_dir = usos.__path__[0]

    for _, module_name, _ in pkgutil.walk_packages([package_dir], prefix="usos."):
        if module_name.endswith('.tools') or module_name.endswith('.prompts') or module_name.endswith('.resources'):
            importlib.import_module(module_name)


class USOSMcp:
    def __init__(self,
                 server_settings: ServerSettings | None = None) -> None:
        self.settings = server_settings or ServerSettings()
        self.mcp = FastMCP("USOS MCP server")

        discover_modules()
        registry.register_to_fastmcp(self.mcp)

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
