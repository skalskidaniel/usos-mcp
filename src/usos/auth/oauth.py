import os
import json
from pathlib import Path
from requests_oauthlib import OAuth1Session
from .storage import save_credentials, load_credentials

REQUEST_TOKEN_URL = "https://usosapps.put.poznan.pl/services/oauth/request_token"
AUTHORIZE_URL = "https://usosapps.put.poznan.pl/services/oauth/authorize"
ACCESS_TOKEN_URL = "https://usosapps.put.poznan.pl/services/oauth/access_token"

SCOPES = "offline_access|studies|grades|student_exams|crstests|other_emails"

# Temporary file storage for request token before PIN verification
REQUEST_TOKEN_FILE = Path(__file__).parent / ".request_token.json"

def _save_request_token(token: str, secret: str) -> None:
    with open(REQUEST_TOKEN_FILE, "w") as f:
        json.dump({"oauth_token": token, "oauth_token_secret": secret}, f)

def _load_request_token() -> tuple[str | None, str | None]:
    if not REQUEST_TOKEN_FILE.exists():
        return None, None
    try:
        with open(REQUEST_TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("oauth_token"), data.get("oauth_token_secret")
    except Exception:
        return None, None

def get_consumer_keys() -> tuple[str, str]:
    key = os.getenv("USOS_API_PUT_CONSUMER_KEY")
    secret = os.getenv("USOS_API_PUT_CONSUMER_SECRET")
    if not key or not secret:
        raise ValueError("USOS_API_PUT_CONSUMER_KEY and USOS_API_PUT_CONSUMER_SECRET must be set in .env")
    return key, secret

def get_authorization_url() -> str:
    """
    Starts the OAuth 1.0a flow and returns the authorization URL.
    """
    client_key, client_secret = get_consumer_keys()
    
    oauth = OAuth1Session(client_key, client_secret=client_secret, callback_uri="oob")
    fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL, data={"scopes": SCOPES})
    
    token = fetch_response.get('oauth_token')
    secret = fetch_response.get('oauth_token_secret')
    _save_request_token(token, secret)
    
    authorization_url = oauth.authorization_url(AUTHORIZE_URL)
    return authorization_url

def verify_pin_and_save_token(pin: str) -> bool:
    """
    Exchanges the PIN (verifier) for long-lived access tokens and saves them.
    """
    token, secret = _load_request_token()
    if not token:
        raise ValueError("No authentication in progress. Start authentication first.")
        
    client_key, client_secret = get_consumer_keys()
    
    oauth = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=token,
        resource_owner_secret=secret,
        verifier=pin
    )
    
    oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    
    save_credentials(
        oauth_tokens.get('oauth_token'), 
        oauth_tokens.get('oauth_token_secret')
    )
    
    # Clear temporary request token
    if REQUEST_TOKEN_FILE.exists():
        REQUEST_TOKEN_FILE.unlink()
    return True

def get_authenticated_session() -> OAuth1Session | None:
    """
    Returns an authenticated OAuth1Session if credentials exist, otherwise None.
    """
    token, token_secret = load_credentials()
    if not token or not token_secret:
        return None
        
    client_key, client_secret = get_consumer_keys()
    
    return OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret
    )
