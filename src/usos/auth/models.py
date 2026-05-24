from pydantic_settings import BaseSettings, SettingsConfigDict

class USOSAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="usos_api_", extra="ignore")

    consumer_key: str | None = None
    consumer_secret: str | None = None
    base_url: str | None = None
    oauth_token: str | None = None
    oauth_token_secret: str | None = None
