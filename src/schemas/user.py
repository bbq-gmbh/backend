import uuid

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
