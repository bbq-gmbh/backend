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


class UserEmployeePatch(BaseModel):
    new_first_name: Optional[str]
    new_last_name: Optional[str]


class UserPatch(BaseModel):
    id: uuid.UUID
    new_username: Optional[str]
    new_employee: Optional[UserEmployeePatch]
