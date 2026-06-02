from enum import StrEnum
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

import os
import json

ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


class AuthStateKey(StrEnum):
    AUTH_STEP = "auth_step"
    BASE_URL = "auth_base_url"
    CONSUMER_KEY = "consumer_key"
    CONSUMER_SECRET = "consumer_secret"
    OAUTH_TOKEN = "oauth_token"
    OAUTH_TOKEN_SECRET = "oauth_token_secret"


def get_storage_dir() -> Path:
    storage_dir_env = os.environ.get("USOS_API_STORAGE_DIR")
    if storage_dir_env:
        return Path(storage_dir_env)
    return Path.home() / ".config" / "usos-mcp" / "store"


def load_auth_config_from_store_sync() -> dict | None:
    storage_dir = get_storage_dir()
    credentials_file = storage_dir / "auth" / "credentials.json"
    if credentials_file.exists():
        try:
            with open(credentials_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("value")
        except Exception:
            pass
    return None


class USOSAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_prefix="usos_api_", extra="ignore"
    )

    consumer_key: str | None = None
    consumer_secret: str | None = None
    base_url: str | None = None
    oauth_token: str | None = None
    oauth_token_secret: str | None = None

    @property
    def is_fully_configured(self) -> bool:
        return all(
            [
                self.consumer_key,
                self.consumer_secret,
                self.base_url,
                self.oauth_token,
                self.oauth_token_secret,
            ]
        )

    @model_validator(mode="after")
    def _fill_from_store(self):
        if not self.is_fully_configured:
            data = load_auth_config_from_store_sync()
            if data:
                if not self.consumer_key:
                    object.__setattr__(
                        self,
                        "consumer_key",
                        data.get("consumer_key") or data.get("USOS_API_CONSUMER_KEY"),
                    )
                if not self.consumer_secret:
                    object.__setattr__(
                        self,
                        "consumer_secret",
                        data.get("consumer_secret")
                        or data.get("USOS_API_CONSUMER_SECRET"),
                    )
                if not self.base_url:
                    object.__setattr__(
                        self,
                        "base_url",
                        data.get("base_url") or data.get("USOS_API_BASE_URL"),
                    )
                if not self.oauth_token:
                    object.__setattr__(
                        self,
                        "oauth_token",
                        data.get("oauth_token") or data.get("USOS_API_OAUTH_TOKEN"),
                    )
                if not self.oauth_token_secret:
                    object.__setattr__(
                        self,
                        "oauth_token_secret",
                        data.get("oauth_token_secret")
                        or data.get("USOS_API_OAUTH_TOKEN_SECRET"),
                    )
        return self
