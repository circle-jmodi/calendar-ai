from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Security
    secret_key: str = "dev-secret-key-change-in-prod"
    encryption_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://calai:calai@db:5432/calai"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Slack
    slack_client_id: str = ""
    slack_client_secret: str = ""
    slack_redirect_uri: str = "http://localhost:8000/auth/slack/callback"
    slack_signing_secret: str = ""
    slack_bot_token: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # App
    frontend_url: str = "http://localhost:5173"
    cloud_run_service_url: str = ""
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
