import uuid

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str


class EmployeeCreateForUser(EmployeeCreate):
    user_id: uuid.UUID
