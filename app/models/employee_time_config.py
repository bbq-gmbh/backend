import uuid
from typing import Optional
from datetime import date, timedelta

from pydantic import BaseModel, field_validator
from sqlmodel import Column, Field, SQLModel, JSON


class EmployeeTimeStoreDayConfigDay(BaseModel):
    work_time: timedelta
    pause_time: timedelta

    @field_validator("work_time", "pause_time")
    @classmethod
    def validate_time_positive_and_minute_quantized(cls, v: timedelta) -> timedelta:
        """Ensure time is positive and quantized to minutes."""
        if v.total_seconds() < 0:
            raise ValueError("Time must be positive")

        return v


type EmployeeTimeStoreDayConfig = dict[int, EmployeeTimeStoreDayConfigDay]


class EmployeeTimeConfig(SQLModel, table=True):
    __tablename__: str = "employee_time_configs"
    start: date = Field(primary_key=True)
    end: Optional[date] = Field(index=True)
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="employees.user_id")
    day_config: EmployeeTimeStoreDayConfig = Field(sa_column=Column(JSON))
