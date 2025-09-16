import uuid
from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    username: str | None = None
    is_superuser: bool | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True
