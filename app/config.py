from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", populate_by_name=True)

    app_name: str = Field(default="Distress Scoring MVP", alias="APP_NAME")

    database_url: str = Field(default="sqlite:///./distress.db", alias="DATABASE_URL")

    # Defaults make local dev & tests work without env vars;
    # production can override via environment variables.
    vertex_project_id: str = Field(default="test-project", alias="VERTEX_PROJECT_ID")
    vertex_location: str = Field(default="us-central1", alias="VERTEX_LOCATION")
    vertex_model_name: str = Field(
        default="gemini-1.5-pro",
        alias="VERTEX_MODEL_NAME",
    )
    vertex_temperature: float = Field(default=0.2, alias="VERTEX_TEMPERATURE")
    vertex_timeout_seconds: int = Field(default=10, alias="VERTEX_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()

