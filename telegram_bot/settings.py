from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None
    admin_tg_ids: str | None = None
    backend_api_url: str = "http://api:8000"
    redis_url: str = "redis://redis:6379/0"


settings = BotSettings()
