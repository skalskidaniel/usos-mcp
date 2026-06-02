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
    logger = logging.getLogger(__name__)
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info("USOS MCP server starting", extra={"started_at": started_at})

    from .auth.models import USOSAuthSettings
    auth_settings = USOSAuthSettings()

    if not all([
        auth_settings.consumer_key,
        auth_settings.consumer_secret,
        auth_settings.oauth_token,
        auth_settings.oauth_token_secret,
        auth_settings.base_url
    ]):
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
                user_name = f"{user_data.get('first_name')} {user_data.get('last_name')}"
                logger.info(f"USOS API connection verified successfully for user: {user_name}")
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
    async def on_list_tools(self, context, call_next):
        tools = await call_next(context)
        from .auth.models import USOSAuthSettings
        settings = USOSAuthSettings()
        is_auth = all([
            settings.consumer_key,
            settings.consumer_secret,
            settings.oauth_token,
            settings.oauth_token_secret,
            settings.base_url
        ])
        if is_auth:
            return [t for t in tools if "auth" not in (t.tags or set())]
        else:
            return [t for t in tools if "auth" in (t.tags or set())]


def create_server() -> FastMCP:
    provider = FileSystemProvider(Path(__file__).parent)
    mcp = FastMCP(
        "USOS MCP server",
        providers=[provider],
        lifespan=app_lifespan,
    )
    mcp.add_middleware(AuthFilterMiddleware())
    return mcp


def main() -> None:
    settings = ServerSettings()
    mcp = create_server()
    kwargs = settings.model_dump()
    if settings.transport == "stdio":
        kwargs.pop("host", None)
        kwargs.pop("port", None)
    mcp.run(**kwargs)