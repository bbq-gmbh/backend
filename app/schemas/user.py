from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserOnly(BaseModel):
    id: uuid.UUID
    username: str
    is_superuser: bool
    created_at: datetime


class UserEmployeeOnly(BaseModel):
    first_name: str
    last_name: str


class UserInfo(UserOnly):
    employee: Optional[UserEmployeeOnly]
