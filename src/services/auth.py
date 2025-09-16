from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pydantic import ValidationError

from src.config.settings import settings
from src.models.user import User
from src.schemas.auth import TokenData
from src.services.user import UserService


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def create_token_pair(self, user: User) -> tuple[str, str]:
        """Creates a pair of access and refresh tokens."""
        access_token = self._create_token(
            user,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            kind="access",
        )
        refresh_token = self._create_token(
            user,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            kind="refresh",
        )
        return access_token, refresh_token

    def create_access_token(self, user: User) -> str:
        """Issues a new access token for a user."""
        return self._create_token(
            user,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            kind="access",
        )

    def _create_token(self, user: User, expires_delta: timedelta, kind: str) -> str:
        """Helper to create a token with a specific expiry."""
        now = datetime.now(timezone.utc)
        to_encode = {
            "sub": str(user.id),
            "val": user.validation_key,
            "iat": now,
            "exp": now + expires_delta,
            "kind": kind,
        }
        return jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def get_token_data(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            return TokenData.model_validate(payload)
        except (jwt.PyJWTError, ValidationError):
            return None

    def get_user_from_token(self, token_data: TokenData) -> Optional[User]:
        user = self.user_service.get_user_by_id(token_data.sub)
        if user is None or user.validation_key != token_data.val:
            return None
        return user
