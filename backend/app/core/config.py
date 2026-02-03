from __future__ import annotations

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    app_name: str = "calculateTA"
    api_prefix: str = "/api"
    environment: str = "development"

    database_url: str

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"
    openai_timeout_seconds: int = 45

    frontend_dist_path: str = "frontend/dist"
    cors_allowed_origins: list[AnyUrl] = []

    optimistic_multiplier: float = 0.85
    pessimistic_multiplier: float = 1.25

    uncertainty_coefficients: dict[str, float] = {
        "known": 1.0,
        "new_tech": 1.5,
    }
    uiux_coefficients: dict[str, float] = {
        "mvp": 1.0,
        "award": 2.5,
    }
    legacy_multiplier: float = 1.3


def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
