from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    validation_key: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str
