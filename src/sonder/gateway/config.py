import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

DEFAULT_CONFIG_PATH = Path.home() / ".sonder" / "config.toml"


class TelegramConfig(BaseModel):
    enabled: bool = False
    bot_token: str | None = None
    allowed_users: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_token_when_enabled(self) -> "TelegramConfig":
        if self.enabled and not self.bot_token:
            raise ValueError("telegram.bot_token is required when telegram is enabled")
        return self


class GatewayAppConfig(BaseModel):
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> GatewayAppConfig:
    config_path = Path(path).expanduser()
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    return GatewayAppConfig.model_validate(data)
