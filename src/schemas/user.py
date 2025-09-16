import uuid

from pydantic import BaseModel


class UsernameBase(BaseModel):
    username: str


class CreateUserRequest(UsernameBase):
    password: str


class UserCreatedResponse(UsernameBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
