from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from src.config.settings import settings
from src.models.user import User
from src.services.user import UserService


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def create_token_pair(self, user: User) -> tuple[str, str]:
        """Creates a pair of access and refresh tokens."""
        access_token = self._create_token(
            user, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = self._create_token(
            user, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        return access_token, refresh_token

    def _create_token(self, user: User, expires_delta: timedelta) -> str:
        """Helper to create a token with a specific expiry."""
        to_encode = {
            "sub": str(user.id),
            "validation_key": user.validation_key,
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
        return jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def get_user_from_token(self, token: str) -> Optional[User]:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get("sub")
            validation_key = payload.get("validation_key")
            if user_id is None or validation_key is None:
                return None

            user = self.user_service.get_user_by_id(user_id)
            if user is None or user.validation_key != validation_key:
                return None
            return user
        except jwt.PyJWTError:
            return None
