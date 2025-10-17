import os

from dotenv import load_dotenv

# Load environment variables from .env file (only if not in test mode)
if os.getenv("TESTING") != "1":
    load_dotenv()


def _get_env(key: str, default: str | None = None) -> str:
    """Gets an environment variable with an optional default."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set.")
    return value


class Settings:
    """Application settings loaded from environment variables."""

    # Database settings
    DATABASE_URL: str = _get_env("DATABASE_URL", "sqlite:///.temp/database.db")

    # JWT settings
    JWT_SECRET_KEY: str = _get_env("JWT_SECRET_KEY", "test-secret-key-change-in-production")
    JWT_ALGORITHM: str = _get_env("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        _get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(_get_env("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


settings = Settings()
