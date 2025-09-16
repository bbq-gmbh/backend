from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TokenKind(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenData(BaseModel):
    sub: str
    token_version: int
    iat: datetime
    exp: datetime
    token_kind: TokenKind


class TokenType(str, Enum):
    BEARER = "bearer"


class Token(BaseModel):
    token: str
    token_type: TokenType = TokenType.BEARER


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: TokenType = TokenType.BEARER


class LoginRequest(BaseModel):
    username: str
    password: str
