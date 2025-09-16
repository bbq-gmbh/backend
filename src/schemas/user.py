import uuid

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserCreatedResponse(BaseModel):
    id: uuid.UUID

    class Config:
        from_attributes = True
