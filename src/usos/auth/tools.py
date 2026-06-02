import asyncio

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from .models import USOSAuthSettings, AuthStateKey
from .utils import get_auth_settings
from requests_oauthlib import OAuth1Session


@tool(
    name="login",
    description="Interactive step-by-step authentication tool. Run this tool with no parameters first to start.",
    tags={"auth"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
    timeout=15,
)
async def login(
    base_url: str | None = None,
    consumer_key: str | None = None,
    consumer_secret: str | None = None,
    pin: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Interactive multi-step OAuth 1.0a authentication flow."""
    current_step = await ctx.get_state(AuthStateKey.AUTH_STEP)

    if current_step not in [
        "AWAITING_BASE_URL",
        "AWAITING_APP_REGISTRATION",
        "AWAITING_PIN",
    ]:
        await ctx.set_state(AuthStateKey.AUTH_STEP, "AWAITING_BASE_URL")
        return {
            "status": "AWAITING_BASE_URL",
            "message": "Please ask the user for their university name. Read the resource `usos://universities/supported` to find the correct `base_url` for that university, then call me again passing `base_url`.",
        }

    if current_step == "AWAITING_BASE_URL":
        if not base_url:
            raise ToolError(
                "Error: `base_url` is required for this step. Please provide the matched `base_url`."
            )

        await ctx.set_state(AuthStateKey.BASE_URL, base_url)
        await ctx.set_state(AuthStateKey.AUTH_STEP, "AWAITING_APP_REGISTRATION")

        return {
            "status": "AWAITING_APP_REGISTRATION",
            "base_url": base_url,
            "message": (
                f"Please instruct the user to visit '{base_url.rstrip('/')}/developers' to register "
                "a new application, and retrieve the `Consumer Key` and `Consumer Secret`. "
                "Once they provide them, call me again passing `consumer_key` and `consumer_secret`."
            ),
        }

    if current_step == "AWAITING_APP_REGISTRATION":
        if not consumer_key or not consumer_secret:
            raise ToolError(
                "Error: Both `consumer_key` and `consumer_secret` are required for this step."
            )

        stored_base_url = await ctx.get_state(AuthStateKey.BASE_URL)
        if not stored_base_url or not isinstance(stored_base_url, str):
            await ctx.set_state(AuthStateKey.AUTH_STEP, "AWAITING_BASE_URL")
            raise ToolError(
                "Session expired or base_url missing. Please start over by providing `base_url`."
            )

        request_token_url = (
            f"{stored_base_url.rstrip('/')}/services/oauth/request_token"
        )
        authorize_url = f"{stored_base_url.rstrip('/')}/services/oauth/authorize"

        oauth = OAuth1Session(
            client_key=consumer_key, client_secret=consumer_secret, callback_uri="oob"
        )

        try:
            await ctx.info("Requesting OAuth request token.")
            scopes = "studies|grades|offline_access"
            fetch_response = await asyncio.to_thread(
                oauth.fetch_request_token,
                f"{request_token_url}?scopes={scopes}",
            )

            resource_owner_key = fetch_response.get("oauth_token")
            resource_owner_secret = fetch_response.get("oauth_token_secret")

            if not resource_owner_key or not resource_owner_secret:
                raise ToolError(
                    "Failed to retrieve valid request tokens from USOS API."
                )

            await ctx.set_state(AuthStateKey.OAUTH_TOKEN, resource_owner_key)
            await ctx.set_state(AuthStateKey.OAUTH_TOKEN_SECRET, resource_owner_secret)
            await ctx.set_state(AuthStateKey.CONSUMER_KEY, consumer_key)
            await ctx.set_state(AuthStateKey.CONSUMER_SECRET, consumer_secret)
            await ctx.set_state(AuthStateKey.AUTH_STEP, "AWAITING_PIN")

            authorization_url = oauth.authorization_url(authorize_url)

            return {
                "status": "AWAITING_PIN",
                "authorize_url": authorization_url,
                "message": (
                    f"Please provide this authorization URL to the user: {authorization_url}\n"
                    "Ask them to log in, authorize the application, and paste the resulting PIN code back to you. "
                    "Once you have the PIN, call me again passing `pin`."
                ),
            }
        except Exception as e:
            await ctx.error(f"OAuth request token error: {e}")
            raise ToolError(f"OAuth request token error: {e}") from e

    if current_step == "AWAITING_PIN":
        if not pin:
            raise ToolError("Error: `pin` is required for this step.")

        stored_base_url = await ctx.get_state(AuthStateKey.BASE_URL)
        c_key = await ctx.get_state(AuthStateKey.CONSUMER_KEY)
        c_secret = await ctx.get_state(AuthStateKey.CONSUMER_SECRET)
        oauth_token = await ctx.get_state(AuthStateKey.OAUTH_TOKEN)
        oauth_token_secret = await ctx.get_state(AuthStateKey.OAUTH_TOKEN_SECRET)

        if not all([stored_base_url, c_key, c_secret, oauth_token, oauth_token_secret]):
            await ctx.set_state(AuthStateKey.AUTH_STEP, "AWAITING_BASE_URL")
            raise ToolError(
                "Session state lost or expired. Please start over by providing `base_url`."
            )

        access_token_url = f"{stored_base_url.rstrip('/')}/services/oauth/access_token"

        oauth = OAuth1Session(
            client_key=c_key,
            client_secret=c_secret,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            verifier=pin,
        )

        try:
            await ctx.info("Requesting OAuth access token.")
            oauth_tokens = await asyncio.to_thread(
                oauth.fetch_access_token,
                access_token_url,
            )

            await ctx.delete_state(AuthStateKey.OAUTH_TOKEN_SECRET)
            await ctx.delete_state(AuthStateKey.OAUTH_TOKEN)
            await ctx.delete_state(AuthStateKey.CONSUMER_KEY)
            await ctx.delete_state(AuthStateKey.CONSUMER_SECRET)
            await ctx.delete_state(AuthStateKey.BASE_URL)
            await ctx.delete_state(AuthStateKey.AUTH_STEP)

            oauth_token = oauth_tokens.get("oauth_token")
            oauth_token_secret = oauth_tokens.get("oauth_token_secret")

            from .utils import save_auth_config

            config_path = await save_auth_config(
                consumer_key=c_key,
                consumer_secret=c_secret,
                base_url=stored_base_url,
                oauth_token=oauth_token,
                oauth_token_secret=oauth_token_secret,
            )

            await ctx.info(
                f"Saved authentication credentials automatically to {config_path}"
            )

            if hasattr(ctx, "send_notification"):
                try:
                    import mcp.types
                    await ctx.send_notification(mcp.types.ToolListChangedNotification())
                    await ctx.info("Sent tool list changed notification to client.")
                except Exception as e:
                    await ctx.warning(f"Could not notify client about changed tools: {e}")

            return {
                "status": "SUCCESS",
                "message": f"Successfully authenticated! Credentials have been saved locally to {config_path}. The server is now ready and fully authenticated.",
            }
        except Exception as e:
            await ctx.error(f"OAuth access token error: {e}")
            raise ToolError(f"OAuth access token error: {e}") from e


@tool(
    name="check_login",
    description="Check if the MCP server is currently authenticated with the USOS API. Use this to verify if the user has completed the setup.",
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
        "destructiveHint": False,
    },
    timeout=15,
)
async def check_login(
    settings: USOSAuthSettings = Depends(get_auth_settings),
    ctx: Context = CurrentContext(),
) -> dict:
    """Verify current USOS API authentication status."""
    if not settings.is_fully_configured:
        await ctx.info("Missing OAuth credentials or base URL.")
        return {
            "authenticated": False,
            "reason": "Missing OAuth credentials or base URL. Run the authenticate_me prompt first.",
        }

    try:
        from .utils import get_authenticated_session

        session = get_authenticated_session()

        test_url = f"{settings.base_url.rstrip('/')}/services/users/user"
        await ctx.info("Checking USOS authentication status.")
        response = await asyncio.to_thread(session.get, test_url, timeout=10)

        if response.status_code == 200:
            user_data = response.json()
            return {
                "authenticated": True,
                "user": f"{user_data.get('first_name')} {user_data.get('last_name')}",
            }
        else:
            raise ToolError(
                f"API returned status {response.status_code}: {response.text}"
            )
    except Exception as e:
        await ctx.error(f"Authentication check failed: {e}")
        raise ToolError(f"Authentication check failed: {e}") from e


@tool(
    name="logout",
    description="Log out and delete stored USOS API authentication credentials from the local configuration store.",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
    timeout=10,
)
async def logout(ctx: Context = CurrentContext()) -> dict:
    """Clear stored OAuth credentials and session state."""
    from .utils import _get_auth_store

    await ctx.delete_state(AuthStateKey.OAUTH_TOKEN_SECRET)
    await ctx.delete_state(AuthStateKey.OAUTH_TOKEN)
    await ctx.delete_state(AuthStateKey.CONSUMER_KEY)
    await ctx.delete_state(AuthStateKey.CONSUMER_SECRET)
    await ctx.delete_state(AuthStateKey.BASE_URL)
    await ctx.delete_state(AuthStateKey.AUTH_STEP)

    store = _get_auth_store()

    try:
        await store.delete("credentials", collection="auth")
        await ctx.info("Deleted credentials from local storage.")

        if hasattr(ctx, "send_notification"):
            try:
                import mcp.types
                await ctx.send_notification(mcp.types.ToolListChangedNotification())
                await ctx.info("Sent tool list changed notification to client.")
            except Exception as e:
                await ctx.warning(f"Could not notify client about changed tools: {e}")

        return {
            "success": True,
            "message": "Authentication credentials cleared successfully. You are now logged out.",
        }
    except Exception:
        return {
            "success": True,
            "message": "No stored credentials found in local configuration store.",
        }
