from sqlmodel import Field, SQLModel




class OvertimeRecord(SQLModel, table=True):
    """
    Represents an overtime record in the database.

    - worked_hours: Net working time after breaks
    - overtime_hours: Positive overtime beyond the expected hours
    - overtimedifference: Net working time minus expected hours (can be negative)
    """

    __tablename__ = "time_records"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date = Field(nullable=False)
    overtime_hours: float = Field(default=0.0)        # Only positive overtime
# Nils bitte Überarbeiten, dass die Overtime richtig gespeichert wird.
