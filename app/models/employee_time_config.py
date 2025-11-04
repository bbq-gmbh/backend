import uuid
from typing import Optional
from datetime import date, time

from pydantic import BaseModel
from sqlmodel import Column, Field, SQLModel, JSON


class EmployeeTimeStoreDayConfigDay(BaseModel):
    work_time: time
    pause_time: time


type EmployeeTimeStoreDayConfig = dict[int, EmployeeTimeStoreDayConfigDay]


class EmployeeTimeConfig(SQLModel, table=True):
    __tablename__: str = "employee_time_configs"
    start: date = Field(primary_key=True)
    end: Optional[date] = Field(index=True)
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="employees.user_id")
    day_config: EmployeeTimeStoreDayConfig = Field(sa_column=Column(JSON))
