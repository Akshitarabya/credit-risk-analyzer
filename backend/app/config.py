"""
Centralized application settings.

All configuration is read from environment variables (with a local .env file
for development). Nothing is hardcoded so the same code works in dev/test/prod
by just changing environment variables.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql://credit_user:credit_pass@localhost:5432/credit_risk_db"

    # --- JWT Auth ---
    jwt_secret_key: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # --- CORS ---
    frontend_origin: str = "http://localhost:5173"

    # --- Groq API (Module 4) ---
    groq_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Settings are cached so the .env file is only parsed once per process,
    and every part of the app shares the exact same config object.
    """
    return Settings()


settings = get_settings()
