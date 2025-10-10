from sqlmodel import Field, SQLModel


class OvertimeRecord(SQLModel, table=True):
    __tablename__ = "time_records"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date = Field(nullable=False)
    overtime_hours: float = Field(default=0.0) 
