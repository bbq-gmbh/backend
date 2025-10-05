from sqlmodel import Field, SQLModel




class OvertimeRecord(SQLModel, table=True):
    """
     Represents an overtime record in the database.

     overtimedifference: overtime difference is the time over the core worktime without the breakes stored in hours as a float.
    """
    __tablename__: str = "time_records"
    id: int = Field(default=None, primary_key=True)
    overtimedifference: float = Field(default=0.0) 
# Nils bitte Überarbeiten, dass die Overtime richtig gespeichert wird.
