from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str | None = None
    claude_model: str = "claude-opus-5-5"
    claude_effort: str = "low"
    max_output_tokens: int = 16000

    shop_name: str = "Lumi Home"
    database_path: str = "./data/shop.db"

    # Safety limits
    max_tool_rounds: int = 6
    max_sessions: int = 500
    max_turns_per_session: int = 40

    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
