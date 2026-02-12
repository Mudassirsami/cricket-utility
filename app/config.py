from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./cricket_club.db"
    MANAGER_PIN_HASH: str = ""
    SCORER_PIN_HASH: str = ""
    RATE_LIMIT: str = "30/minute"
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_EMAIL: str = "mailto:admin@aljinnahcc.com"
    ENVIRONMENT: str = "development"  # development, staging, production
    SECRET_KEY: str = "your-secret-key-change-in-production"  # Add for JWT/tokens if needed
    LOG_LEVEL: str = "INFO"
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
