"""
app/config/settings.py
─────────────────────
Application-wide configuration loaded from environment variables using
Pydantic BaseSettings.  Values can be overridden via a .env file.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object.  All fields map 1-to-1 to env vars."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = Field(default="Product Sentiment Analyzer")
    app_version: str = Field(default="1.0.0")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = Field(default="change-me-in-production")
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="product_sentiment_db")
    mongodb_max_pool_size: int = Field(default=10)
    mongodb_min_pool_size: int = Field(default=1)

    # ── Scraper ───────────────────────────────────────────────────────────────
    scraper_headless: bool = Field(default=True)
    scraper_timeout: int = Field(default=30)
    scraper_delay_min: float = Field(default=2.0)
    scraper_delay_max: float = Field(default=5.0)
    scraper_max_retries: int = Field(default=3)

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    log_rotation: str = Field(default="10 MB")
    log_retention: str = Field(default="7 days")

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug(cls, v: Any) -> bool:
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"release", "production", "prod"}:
                return False
        return v

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def validate_allowed_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            # Parse JSON if it's formatted as a JSON list, e.g. ["http://localhost"]
            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except Exception:
                    pass
            # Fallback to comma-separated values
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton (avoids re-reading .env on every call)."""
    return Settings()
