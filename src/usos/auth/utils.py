from requests_oauthlib import OAuth1Session
from .models import USOSAuthSettings

def get_authenticated_session() -> OAuth1Session:
    """Returns an authenticated OAuth1Session using environment variables."""
    settings = USOSAuthSettings()
    
    if not all([
        settings.consumer_key, 
        settings.consumer_secret, 
        settings.oauth_token, 
        settings.oauth_token_secret
    ]):
        raise ValueError("Missing OAuth credentials in environment variables.")

    return OAuth1Session(
        client_key=settings.consumer_key,
        client_secret=settings.consumer_secret,
        resource_owner_key=settings.oauth_token,
        resource_owner_secret=settings.oauth_token_secret
    )
