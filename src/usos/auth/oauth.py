import os
import json
from pathlib import Path
from requests_oauthlib import OAuth1Session
from .storage import save_credentials, load_credentials

SCOPES = "offline_access|studies|grades|student_exams|crstests|other_emails"

# Temporary file storage for request token before PIN verification
REQUEST_TOKEN_FILE = Path(__file__).parent / ".request_token.json"
UNIVERSITY_CONFIG_FILE = Path(__file__).parent / "university.json"

def set_base_url(base_url: str) -> None:
    with open(UNIVERSITY_CONFIG_FILE, "w") as f:
        json.dump({"base_url": base_url}, f)

def get_base_url() -> str:
    if not UNIVERSITY_CONFIG_FILE.exists():
        raise ValueError("University not set. Please call `set_university` first.")
    with open(UNIVERSITY_CONFIG_FILE, "r") as f:
        data = json.load(f)
        return data["base_url"].rstrip("/")

def _get_urls() -> tuple[str, str, str]:
    base = get_base_url()
    return (
        f"{base}/services/oauth/request_token",
        f"{base}/services/oauth/authorize",
        f"{base}/services/oauth/access_token",
    )

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
    req_url, auth_url, _ = _get_urls()
    
    oauth = OAuth1Session(client_key, client_secret=client_secret, callback_uri="oob")
    fetch_response = oauth.fetch_request_token(req_url, data={"scopes": SCOPES})
    
    token = fetch_response.get('oauth_token')
    secret = fetch_response.get('oauth_token_secret')
    _save_request_token(token, secret)
    
    authorization_url = oauth.authorization_url(auth_url)
    return authorization_url

def verify_pin_and_save_token(pin: str) -> bool:
    """
    Exchanges the PIN (verifier) for long-lived access tokens and saves them.
    """
    token, secret = _load_request_token()
    if not token:
        raise ValueError("No authentication in progress. Start authentication first.")
        
    client_key, client_secret = get_consumer_keys()
    _, _, access_url = _get_urls()
    
    oauth = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=token,
        resource_owner_secret=secret,
        verifier=pin
    )
    
    oauth_tokens = oauth.fetch_access_token(access_url)
    
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
