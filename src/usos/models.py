from pydantic import BaseModel, Field, PositiveInt, field_validator, IPvAnyAddress, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Callable, Any


class ServerSettings(BaseSettings):
    """Used for local development only"""
    model_config = SettingsConfigDict(env_prefix="fast_mcp_", extra="ignore")

    transport: Literal["stdio", "http", "sse", "streamable-http"] = Field(default="stdio")
    host: str = Field(default="0.0.0.0")
    port: PositiveInt = Field(default=8000)

    @field_validator("host")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return str(IPvAnyAddress(v))


class Tool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    func: Callable[..., Any]
    name: str | None = None
    description: str | None = None


class Prompt(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    func: Callable[..., Any]
    name: str | None = None
    description: str | None = None

class Resource(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    func: Callable[..., Any]
    uri: str
    name: str | None = None
    description: str | None = None