import uuid
from datetime import date
from typing import Optional

from sqlmodel import Session, select

from app.models.overtime import OvertimeRecord


class OvertimeRecordRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, overtime_record: OvertimeRecord) -> OvertimeRecord:
        """Create a new overtime record."""
        self.session.add(overtime_record)
        self.session.flush()
        self.session.refresh(overtime_record)
        return overtime_record

    def get_by_id(self, record_id: int) -> Optional[OvertimeRecord]:
        """Get an overtime record by ID."""
        return self.session.get(OvertimeRecord, record_id)

    def get_by_user_id(self, user_id: uuid.UUID) -> list[OvertimeRecord]:
        """Get all overtime records for a specific user."""
        statement = select(OvertimeRecord).where(OvertimeRecord.user_id == user_id)
        return list(self.session.exec(statement).all())

    def get_by_user_and_date_range(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[OvertimeRecord]:
        """Get overtime records for a user within a date range."""
        statement = (
            select(OvertimeRecord)
            .where(OvertimeRecord.user_id == user_id)
            .where(OvertimeRecord.date >= start_date)
            .where(OvertimeRecord.date <= end_date)
            .order_by(OvertimeRecord.date)
        )
        return list(self.session.exec(statement).all())

    def get_all(self) -> list[OvertimeRecord]:
        """Get all overtime records."""
        statement = select(OvertimeRecord)
        return list(self.session.exec(statement).all())

    def update(self, overtime_record: OvertimeRecord) -> OvertimeRecord:
        """Update an existing overtime record."""
        self.session.add(overtime_record)
        self.session.flush()
        self.session.refresh(overtime_record)
        return overtime_record

    def delete(self, record_id: int) -> bool:
        """Delete an overtime record by ID."""
        record = self.get_by_id(record_id)
        if record:
            self.session.delete(record)
            return True
        return False

    def get_total_overtime_by_user(self, user_id: uuid.UUID) -> float:
        """Calculate total overtime hours for a user."""
        records = self.get_by_user_id(user_id)
        return sum(record.overtime_hours for record in records)
