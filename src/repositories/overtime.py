from sqlmodel import Field, SQLModel


class TimeRecord(SQLModel, table=True):
    __tablename__: str = "time_records"
    id: int = Field(default=None, primary_key=True)
Services:
from sqlmodel import Field, SQLModel


class OvertimeRecord(SQLModel, table=True):
    __tablename__: str = "time_records"
    id: int = Field(default=None, primary_key=True)

