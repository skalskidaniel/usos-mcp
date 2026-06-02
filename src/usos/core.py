from datetime import datetime, timezone
import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider
from fastmcp.server.lifespan import lifespan
from fastmcp.server.middleware import Middleware

from .models import ServerSettings


@lifespan
async def app_lifespan(server):
    """Lifecycle manager for the USOS MCP server."""
    logger = logging.getLogger(__name__)
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info("USOS MCP server starting", extra={"started_at": started_at})

    # Lazy import to avoid circular dependency with auth module
    from .auth.models import USOSAuthSettings

    auth_settings = USOSAuthSettings()

    if not auth_settings.is_fully_configured:
        logger.warning(
            "USOS API credentials or base URL are missing from the environment. "
            "Please configure USOS_API_CONSUMER_KEY, USOS_API_CONSUMER_SECRET, "
            "USOS_API_OAUTH_TOKEN, USOS_API_OAUTH_TOKEN_SECRET, and USOS_API_BASE_URL, "
            "or use the authentication setup prompt to authorize."
        )
    else:
        logger.info("USOS API credentials detected. Verifying connection...")
        try:
            import asyncio
            from .auth.utils import get_authenticated_session

            session = get_authenticated_session()
            test_url = f"{auth_settings.base_url.rstrip('/')}/services/users/user"
            response = await asyncio.to_thread(session.get, test_url, timeout=5.0)
            if response.status_code == 200:
                user_data = response.json()
                user_name = (
                    f"{user_data.get('first_name')} {user_data.get('last_name')}"
                )
                logger.info(
                    f"USOS API connection verified successfully for user: {user_name}"
                )
            else:
                logger.warning(
                    f"USOS API returned status code {response.status_code} during startup check. "
                    f"Details: {response.text}"
                )
        except Exception as e:
            logger.warning(f"Failed to verify USOS API connection at startup: {e}")

    try:
        yield {"started_at": started_at}
    finally:
        logger.info("USOS MCP server stopping")


class AuthFilterMiddleware(Middleware):
    """Middleware to filter tools based on authentication status."""

    async def on_list_tools(self, context, call_next):
        tools = await call_next(context)
        # Lazy import to avoid circular dependency with auth module
        from .auth.models import USOSAuthSettings

        settings = USOSAuthSettings()
        if settings.is_fully_configured:
            return [t for t in tools if "auth" not in (t.tags or set())]
        else:
            return [t for t in tools if "auth" in (t.tags or set())]


def create_server() -> FastMCP:
    """Build and return the FastMCP application with providers and middleware."""
    provider = FileSystemProvider(Path(__file__).parent)
    mcp = FastMCP(
        "USOS MCP server",
        providers=[provider],
        lifespan=app_lifespan,
    )
    mcp.add_middleware(AuthFilterMiddleware())
    return mcp


def main() -> None:
    """CLI entry point — configure transport settings and start the server."""
    settings = ServerSettings()
    mcp = create_server()
    kwargs = settings.model_dump()
    if settings.transport == "stdio":
        kwargs.pop("host", None)
        kwargs.pop("port", None)
    mcp.run(**kwargs)
