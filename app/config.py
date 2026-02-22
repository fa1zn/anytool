"""Application configuration from environment."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    openai_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
