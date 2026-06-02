import asyncio

from fastmcp.dependencies import CurrentContext, Depends
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from .models import USOSAuthSettings
from .utils import get_auth_settings
from requests_oauthlib import OAuth1Session

#TODO adjust descriptions

@tool(
    name="get_oauth_request_token",
    description="Step 1 of OAuth 1.0a: Get the request token and authorize URL. Returns oauth_token, oauth_token_secret, and authorize_url. The oauth_token_secret is also stored in session state for step 2.",
    tags={"auth"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def get_oauth_request_token( #TODO rename it
    base_url: str, #TODO is it necessary?
    settings: USOSAuthSettings = Depends(get_auth_settings),
    ctx: Context = CurrentContext(),
) -> dict:
    
    c_key = settings.consumer_key
    c_secret = settings.consumer_secret
    
    if not c_key or not c_secret:
        await ctx.warning("Missing OAuth consumer credentials.")
        raise ToolError("Consumer key and secret are required. Provide them as arguments or set them in the environment.")
    
    request_token_url = f"{base_url.rstrip('/')}/services/oauth/request_token"
    authorize_url = f"{base_url.rstrip('/')}/services/oauth/authorize"

    oauth = OAuth1Session(
        client_key=c_key, 
        client_secret=c_secret, 
        callback_uri="oob"
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
        
        if resource_owner_key:
            await ctx.set_state("oauth_token", resource_owner_key)
            await ctx.info("Stored oauth_token in session state")
        else:
            await ctx.warning("Received empty oauth_token_secret from USOS")
        
        if resource_owner_secret:
            await ctx.set_state("oauth_token_secret", resource_owner_secret)
            await ctx.info("Stored oauth_token_secret in session state.")
        else:
            await ctx.warning("Received empty oauth_token_secret from USOS.")
        
        authorization_url = oauth.authorization_url(authorize_url)
        
        return {
            "authorize_url": authorization_url
        }
    except Exception as e:
        await ctx.error(f"OAuth request token error: {e}")
        raise ToolError(f"OAuth request token error: {e}") from e

@tool(
    name="get_oauth_access_token", #TODO rename it
    description="Step 2 of OAuth 1.0a: Exchange the request token and PIN for a persistent access token. Reads oauth_token_secret from session state.",
    tags={"auth"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def get_oauth_access_token(
    base_url: str, #TODO is it necessary?
    pin: str,
    settings: USOSAuthSettings = Depends(get_auth_settings),
    ctx: Context = CurrentContext(),
) -> dict:
    
    c_key = settings.consumer_key
    c_secret = settings.consumer_secret
    
    #TODO improve missing keys handling logic
    if not c_key or not c_secret:
        await ctx.warning("Missing OAuth consumer credentials.")
        raise ToolError("Consumer key and secret are required. Provide them as arguments or set them in the environment.")

    oauth_token_secret = await ctx.get_state("oauth_token_secret")
    if not oauth_token_secret:
        await ctx.error("Missing oauth_token_secret in session state.")
        raise ToolError(
            "oauth_token_secret not found in session state. Run get_oauth_request_token in the same session first."
        )
    if not isinstance(oauth_token_secret, str):
        await ctx.error("Invalid oauth_token_secret stored in session state.")
        raise ToolError("oauth_token_secret in session state is invalid.")
    
    oauth_token = await ctx.get_state("oauth_token")
    if not oauth_token:
        await ctx.error("Missing oauth_token in session state.")
        raise ToolError(
            "oauth_token not found in session state. Run get_oauth_request_token in the same session first."
        )
    if not isinstance(oauth_token, str):
        await ctx.error("Invalid oauth_token stored in session state.")
        raise ToolError("oauth_token in session state is invalid.")
    
    access_token_url = f"{base_url.rstrip('/')}/services/oauth/access_token"

    oauth = OAuth1Session(
        client_key=c_key,
        client_secret=c_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        verifier=pin
    )

    try:
        await ctx.info("Requesting OAuth access token.")
        oauth_tokens = await asyncio.to_thread(
            oauth.fetch_access_token,
            access_token_url,
        )
        await ctx.delete_state("oauth_token_secret")
        return {
            "oauth_token": oauth_tokens.get("oauth_token"),
            "oauth_token_secret": oauth_tokens.get("oauth_token_secret")
        }
    except Exception as e:
        await ctx.error(f"OAuth access token error: {e}")
        raise ToolError(f"OAuth access token error: {e}") from e

@tool(
    name="check_authentication",
    description="Check if the MCP server is currently authenticated with the USOS API. Use this to verify if the user has completed the setup.",
    tags={"auth"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": False,
        "destructiveHint": False
    },
)
async def check_authentication(
    settings: USOSAuthSettings = Depends(get_auth_settings),
    ctx: Context = CurrentContext()
) -> dict:
    
    if not all([
        settings.consumer_key, 
        settings.consumer_secret, 
        settings.oauth_token, 
        settings.oauth_token_secret,
        settings.base_url
    ]):
        await ctx.info("Missing OAuth credentials or base URL in environment variables.")
        return {
            "authenticated": False, 
            "reason": "Missing OAuth credentials or base URL in environment variables. Run the setup_usos_authentication prompt first."
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
                "user": f"{user_data.get('first_name')} {user_data.get('last_name')}"
            }
        else:
            return {
                "authenticated": False,
                "reason": f"API returned status {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        await ctx.error(f"Authentication check failed: {e}")
        raise ToolError(f"Authentication check failed: {e}") from e
