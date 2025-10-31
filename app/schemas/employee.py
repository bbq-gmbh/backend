import uuid

from pydantic import BaseModel

from .user import UserOnly, UserEmployeeOnly


class EmployeeCreate(BaseModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str


class EmployeeInfo(UserOnly):
    employee: UserEmployeeOnly
