import uuid
from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class Employee(BaseModel):
    first_name: str
    last_name: str


class MeUser(BaseModel):
    id: uuid.UUID
    username: str
    is_superuser: bool
    created_at: datetime
    employee: Optional[Employee]
