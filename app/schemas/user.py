import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str | None = None
    is_superuser: bool | None = None
    created_at: datetime | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
