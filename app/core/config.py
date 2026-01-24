from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Booked Table"
    environment: str = "development"
    debug: bool = False
    secret_key: str = "change-me"
    session_https_only: bool = False

    database_url: str = "postgresql+psycopg2://booked:booked@postgres:5432/booked"
    redis_url: str = "redis://redis:6379/0"

    admin_email: str = "owner@example.com"
    admin_password_hash: str = "$2b$12$8OvWDKYUuX7n3Hisb1lTPeDTSWC.vF1ae4dhY93vwMS2jkwC0GaYm"
    admin_api_key: str = "change-me"

    timezone: str = "Europe/Oslo"
    booking_price_rub: int = 1000

    tbank_enabled: bool = False
    tbank_terminal_key: str = ""
    tbank_password: str = ""
    tbank_notification_url: str = ""
    tbank_success_url: str = ""
    tbank_fail_url: str = ""
    tbank_redirect_due_minutes: int = 30

    calendar_enabled: bool = False
    yandex_login: str = ""
    yandex_app_password: str = ""
    yandex_calendar_url: str = "https://caldav.yandex.ru"
    yandex_calendar_mapping: str | None = None

    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None
    admin_tg_ids: str | None = None
    backend_api_url: str = "http://api:8000"


settings = Settings()


class AdminUser(BaseModel):
    email: str
    password_hash: str


admin_user = AdminUser(email=settings.admin_email, password_hash=settings.admin_password_hash)
