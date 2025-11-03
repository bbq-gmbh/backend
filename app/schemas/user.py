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
    employee: Optional[UserEmployeeOnly] = None


class UserEmployeePatch(BaseModel):
    new_first_name: Optional[str] = None
    new_last_name: Optional[str] = None
    new_supervisor_id: Optional[uuid.UUID] = None


class UserPatch(BaseModel):
    new_username: Optional[str] = None
    new_is_superuser: Optional[bool] = None
    new_employee: Optional[UserEmployeePatch] = None
