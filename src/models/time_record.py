from sqlmodel import Field, SQLModel


class TimeRecord(SQLModel, table=True):
    __tablename__: str = "time_records"
    id: int = Field(default=None, primary_key=True)
