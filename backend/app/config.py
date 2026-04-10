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
        extra="ignore",
    )

    # Neo4j database settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    neo4j_max_pool_size: int = 50

    # Clerk authentication settings
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwt_issuer: str = ""
    clerk_jwks_url: str = ""

    anthropic_api_key: str = ""
    # Paddle billing settings
    paddle_webhook_secret: str = ""
    paddle_api_key: str = ""
    paddle_api_url: str = "https://sandbox-api.paddle.com"
    paddle_price_starter: str = ""
    paddle_price_professional: str = ""
    paddle_price_business: str = ""
    cors_origins: str = "http://localhost:5173,https://app.kerf.build"
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
