import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    def __init__(self):
        self.APP_NAME: str = os.getenv("APP_NAME", "fs-backend")
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.DATABASE_URL: str = database_url

        jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable not set")
        self.JWT_SECRET_KEY: str = jwt_secret_key

        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        # CORS_ORIGINS should be a comma-separated string in the .env file
        self.CORS_ORIGINS: list[str] = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000"
        ).split(",")


settings = Settings()
