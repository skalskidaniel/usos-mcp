# from pathlib import Path
from pydantic import Field, PositiveInt, field_validator, IPvAnyAddress
from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Literal

# ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="fast_mcp_", extra="ignore")

    transport: Literal["stdio", "http", "sse", "streamable-http"] = Field(default="stdio")
    host: str = Field(default="0.0.0.0")
    port: PositiveInt = Field(default=8000)

    @field_validator("host")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return str(IPvAnyAddress(v))