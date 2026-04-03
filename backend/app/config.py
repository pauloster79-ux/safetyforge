"""Application configuration via pydantic-settings."""

import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    google_cloud_project: str = "safetyforge-prod"
    anthropic_api_key: str = ""
    lemon_squeezy_webhook_secret: str = ""
    lemon_squeezy_api_key: str = ""
    cors_origins: str = "http://localhost:5173,https://app.safetyforge.com"
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
