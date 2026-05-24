from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


class USOSAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_PATH, env_prefix="usos_api_", extra="ignore")

    consumer_key: str | None = None
    consumer_secret: str | None = None
    base_url: str | None = None
    oauth_token: str | None = None
    oauth_token_secret: str | None = None
