from typing import Callable, Any
from .models import Tool, Prompt, Resource

class MCPRegistry:
    def __init__(self):
        self.tools: list[Tool] = []
        self.prompts: list[Prompt] = []
        self.resources: list[Resource] = []

    def tool(self, name: str | None = None, description: str | None = None):
        """Decorator to register a tool."""
        def decorator(func: Callable[..., Any]):
            self.tools.append(Tool(func=func, name=name, description=description))
            return func
        return decorator

    def prompt(self, name: str | None = None, description: str | None = None):
        """Decorator to register a prompt."""
        def decorator(func: Callable[..., Any]):
            self.prompts.append(Prompt(func=func, name=name, description=description))
            return func
        return decorator

    def resource(self, uri: str, name: str | None = None, description: str | None = None):
        """Decorator to register a resource."""
        def decorator(func: Callable[..., Any]):
            self.resources.append(Resource(func=func, uri=uri, name=name, description=description))
            return func
        return decorator

    def register_to_fastmcp(self, mcp_app):
        """Binds all registered tools and prompts to the actual FastMCP app."""
        for t in self.tools:
            mcp_app.tool(name=t.name, description=t.description)(t.func)
        for p in self.prompts:
            mcp_app.prompt(name=p.name, description=p.description)(p.func)
        for r in self.resources:
            mcp_app.resource(r.uri, name=r.name, description=r.description)(r.func)


registry = MCPRegistry()
