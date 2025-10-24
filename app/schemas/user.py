import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    is_superuser: bool
    created_at: datetime


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
