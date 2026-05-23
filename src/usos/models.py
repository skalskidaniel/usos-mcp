from pathlib import Path
from pydantic import BaseModel, Field, PositiveInt, field_validator, IPvAnyAddress, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Literal

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
UNIVERSITIES_FILE = Path(__file__).parent / "universities.json"

class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="fast_mcp_", extra="ignore")

    transport: Literal["stdio", "http", "sse", "streamable-http"] = Field(default="http")
    host: str = Field(default="0.0.0.0")
    port: PositiveInt = Field(default=8000)

    @field_validator("host")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return str(IPvAnyAddress(v))


class UniversityCredentials(BaseModel):
    consumer_key: str
    consumer_secret: str

class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="usos_api_", extra="allow")

    credentials: dict[str, UniversityCredentials] = Field(default_factory=dict)

    @model_validator(mode="after")
    def parse_dynamic_credentials(self):
        creds = {}
        if self.model_extra:
            for key, value in self.model_extra.items():
                if key.endswith("_consumer_key"):
                    uni_key = key.replace("_consumer_key", "")
                    secret_key = f"{uni_key}_consumer_secret"
                    
                    if secret_key in self.model_extra:
                        creds[uni_key.upper()] = UniversityCredentials(
                            consumer_key=value,
                            consumer_secret=self.model_extra[secret_key]
                        )
        self.credentials = creds
        return self
