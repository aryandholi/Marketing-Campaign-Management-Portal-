"""
Application configuration using Pydantic Settings.

Loads environment variables from .env file and provides
typed access to all configuration values.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings with environment variable binding."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars (prevents startup errors)
    )

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./campaign_portal.db"

    # ── JWT Authentication ────────────────────────────────────────────────
    jwt_secret_key: str = "dev-secret-key-replace-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # ── Application ──────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    # Allow all origins by default — restrict in production via env var
    cors_origins: str = "*"
    google_client_id: str = "1089893144212-0btqbj2vorhrnvnm21f5bpq02f1b8ta9.apps.googleusercontent.com"

    # ── SMTP Email (real sending) ───────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Nexus Portal"
    smtp_use_tls: bool = True

    # ── Twilio SMS (real sending) ───────────────────────────────────────
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    @property
    def smtp_configured(self) -> bool:
        """True when all SMTP credentials are provided."""
        return bool(
            self.smtp_host
            and self.smtp_username
            and self.smtp_password
            and self.smtp_from_email
        )

    @property
    def twilio_configured(self) -> bool:
        """True when Twilio credentials are provided."""
        return bool(
            self.twilio_account_sid
            and self.twilio_auth_token
            and self.twilio_from_number
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton to avoid re-reading env on every request."""
    return Settings()
