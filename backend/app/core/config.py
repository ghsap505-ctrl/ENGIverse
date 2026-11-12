"""Centralised, validated configuration (12-factor: environment variables).

There are deliberately NO defaults for secrets. The application refuses to
start without an explicit DATABASE_URL that contains a password.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.validators import mask_database_url, parse_cors_origins, validate_database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",            # compose-only vars (POSTGRES_*) are ignored
        hide_input_in_errors=True,  # never echo raw values (may contain secrets)
    )

    app_name: str = "ENGIverse API"
    app_version: str = "0.1.2"
    app_env: Literal["development", "test", "production"] = "development"

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # Required, no default. Must be postgresql+psycopg://user:password@host:port/db
    database_url: SecretStr
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=200)
    db_pool_timeout: int = Field(default=30, ge=1, le=300)
    db_pool_recycle: int = Field(default=1800, ge=-1)
    db_connect_timeout: int = Field(default=5, ge=1, le=60)
    db_echo: bool = False

    # Comma-separated bare origins. Empty = no cross-origin access.
    cors_origins: str = ""

    # None => enabled outside production, disabled in production.
    docs_enabled: bool | None = None

    @model_validator(mode="after")
    def _validate_security_sensitive_values(self) -> "Settings":
        validate_database_url(
            self.database_url.get_secret_value(), production=self.is_production
        )
        parse_cors_origins(self.cors_origins)
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return parse_cors_origins(self.cors_origins)

    @property
    def docs_are_enabled(self) -> bool:
        return self.docs_enabled if self.docs_enabled is not None else not self.is_production

    @property
    def safe_database_url(self) -> str:
        return mask_database_url(self.database_url.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment
