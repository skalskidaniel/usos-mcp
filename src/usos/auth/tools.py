from usos.registry import registry
from .models import USOSAuthSettings
from requests_oauthlib import OAuth1Session

@registry.tool(
    name="get_oauth_request_token",
    description="Step 1 of OAuth 1.0a: Get the request token and authorize URL. Returns oauth_token, oauth_token_secret, and authorize_url. Note: You must save the oauth_token_secret in your context memory to use it in step 2."
)
def get_oauth_request_token(base_url: str, consumer_key: str | None = None, consumer_secret: str | None = None) -> dict:
    settings = USOSAuthSettings()
    
    c_key = consumer_key or settings.consumer_key
    c_secret = consumer_secret or settings.consumer_secret
    
    if not c_key or not c_secret:
        return {"error": "Consumer key and secret are required. Provide them as arguments or set them in the environment."}
    
    request_token_url = f"{base_url.rstrip('/')}/services/oauth/request_token"
    authorize_url = f"{base_url.rstrip('/')}/services/oauth/authorize"

    oauth = OAuth1Session(
        client_key=c_key, 
        client_secret=c_secret, 
        callback_uri="oob"
    )
    
    try:
        scopes = "studies|grades|offline_access"
        fetch_response = oauth.fetch_request_token(f"{request_token_url}?scopes={scopes}")
        
        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        
        authorization_url = oauth.authorization_url(authorize_url)
        
        return {
            "oauth_token": resource_owner_key,
            "oauth_token_secret": resource_owner_secret,
            "authorize_url": authorization_url
        }
    except Exception as e:
        return {"error": str(e)}

@registry.tool(
    name="get_oauth_access_token",
    description="Step 2 of OAuth 1.0a: Exchange the request token and PIN for a persistent access token. Returns oauth_token and oauth_token_secret."
)
def get_oauth_access_token(base_url: str, oauth_token: str, oauth_token_secret: str, pin: str, consumer_key: str | None = None, consumer_secret: str | None = None) -> dict:
    settings = USOSAuthSettings()
    
    c_key = consumer_key or settings.consumer_key
    c_secret = consumer_secret or settings.consumer_secret
    
    if not c_key or not c_secret:
        return {"error": "Consumer key and secret are required. Provide them as arguments or set them in the environment."}
    
    access_token_url = f"{base_url.rstrip('/')}/services/oauth/access_token"

    oauth = OAuth1Session(
        client_key=c_key,
        client_secret=c_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        verifier=pin
    )

    try:
        oauth_tokens = oauth.fetch_access_token(access_token_url)
        return {
            "oauth_token": oauth_tokens.get("oauth_token"),
            "oauth_token_secret": oauth_tokens.get("oauth_token_secret")
        }
    except Exception as e:
        return {"error": str(e)}

@registry.tool(
    name="check_authentication",
    description="Check if the MCP server is currently authenticated with the USOS API. Use this to verify if the user has completed the setup."
)
def check_authentication() -> dict:
    settings = USOSAuthSettings()
    
    if not all([
        settings.consumer_key, 
        settings.consumer_secret, 
        settings.oauth_token, 
        settings.oauth_token_secret,
        settings.base_url
    ]):
        return {
            "authenticated": False, 
            "reason": "Missing OAuth credentials or base URL in environment variables. Run the setup_usos_authentication prompt first."
        }
    
    try:
        from .utils import get_authenticated_session
        session = get_authenticated_session()

        test_url = f"{settings.base_url.rstrip('/')}/services/users/user"
        response = session.get(test_url, timeout=10)
        
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
        return {
            "authenticated": False,
            "reason": str(e)
        }
