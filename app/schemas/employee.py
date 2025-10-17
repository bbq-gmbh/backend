import uuid

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str
