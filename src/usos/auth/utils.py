from pathlib import Path
import os

from fastmcp import Context
from requests_oauthlib import OAuth1Session
from .models import USOSAuthSettings, get_storage_dir, AuthStateKey


def get_authenticated_session() -> OAuth1Session:
    """Create an OAuth1Session from stored or environment credentials."""
    settings = USOSAuthSettings()

    if not all(
        [
            settings.consumer_key,
            settings.consumer_secret,
            settings.oauth_token,
            settings.oauth_token_secret,
        ]
    ):
        raise ValueError(
            "Missing OAuth credentials. Please configure them in the environment or run the authentication setup."
        )

    return OAuth1Session(
        client_key=settings.consumer_key,
        client_secret=settings.consumer_secret,
        resource_owner_key=settings.oauth_token,
        resource_owner_secret=settings.oauth_token_secret,
    )


def get_auth_settings() -> USOSAuthSettings:
    """Dependency-injection factory for USOSAuthSettings."""
    return USOSAuthSettings()


def _get_auth_store():
    from key_value.aio.stores.filetree import (
        FileTreeStore,
        FileTreeV1KeySanitizationStrategy,
        FileTreeV1CollectionSanitizationStrategy,
    )

    storage_dir = get_storage_dir()
    storage_dir.mkdir(parents=True, exist_ok=True)

    return FileTreeStore(
        data_directory=storage_dir,
        key_sanitization_strategy=FileTreeV1KeySanitizationStrategy(storage_dir),
        collection_sanitization_strategy=FileTreeV1CollectionSanitizationStrategy(
            storage_dir
        ),
    )


async def save_auth_config(
    consumer_key: str,
    consumer_secret: str,
    base_url: str,
    oauth_token: str,
    oauth_token_secret: str,
) -> Path:
    """Persist OAuth credentials to the local file-based store."""
    storage_dir = get_storage_dir()
    store = _get_auth_store()

    config_data = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "base_url": base_url,
        "oauth_token": oauth_token,
        "oauth_token_secret": oauth_token_secret,
    }

    await store.put("credentials", config_data, collection="auth")

    credentials_file = storage_dir / "auth" / "credentials.json"
    try:
        if os.name != "nt" and credentials_file.exists():
            credentials_file.chmod(0o600)
    except Exception:
        pass

    return credentials_file


async def clear_auth_context(ctx: Context):
    import asyncio
    await asyncio.gather(
        ctx.delete_state(AuthStateKey.OAUTH_TOKEN_SECRET),
        ctx.delete_state(AuthStateKey.OAUTH_TOKEN),
        ctx.delete_state(AuthStateKey.CONSUMER_KEY),
        ctx.delete_state(AuthStateKey.CONSUMER_SECRET),
        ctx.delete_state(AuthStateKey.BASE_URL),
        ctx.delete_state(AuthStateKey.AUTH_STEP),
        return_exceptions=True,
    )
