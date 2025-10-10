import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _get_required_env(key: str) -> str:
    """Gets an environment variable, raising an error if it's not set."""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set.")
    return value


class Settings:
    """Application settings loaded from environment variables."""

    # Application settings
    DEBUG: bool = _get_required_env("DEBUG").lower() in ("true", "1", "t")

    # Database settings
    DATABASE_URL: str = _get_required_env("DATABASE_URL")

    # JWT settings
    JWT_SECRET_KEY: str = _get_required_env("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = _get_required_env("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        _get_required_env("ACCESS_TOKEN_EXPIRE_MINUTES")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(_get_required_env("REFRESH_TOKEN_EXPIRE_DAYS"))

    # CORS settings
    CORS_ORIGINS: list[str] = _get_required_env("CORS_ORIGINS").split(",")


settings = Settings()
