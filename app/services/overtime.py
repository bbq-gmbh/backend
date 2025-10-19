import uuid
from datetime import date, datetime, time
from typing import Optional

from app.models.overtime import OvertimeRecord
from app.models.user import User
from app.repositories.overtime import OvertimeRecordRepository
from app.schemas.overtime import OvertimeRecordCreate, OvertimeRecordUpdate


class OvertimeRecordService:
    def __init__(self, overtime_record_repository: OvertimeRecordRepository) -> None:
        self.overtime_record_repository = overtime_record_repository

    def create_overtime_record(
        self,
        user: User,
        record_data: OvertimeRecordCreate,
    ) -> OvertimeRecord:
        """
        Creates an overtime record for a user based on their work times and breaks.
        
        Args:
            user (User): The user for whom the overtime record is being created.
            record_data (OvertimeRecordCreate): The overtime record data containing work times.
            
        Returns:
            OvertimeRecord: The created overtime record.
        """
        # Calculate total work time
        work_start_dt = datetime.combine(record_data.date, record_data.work_start)
        work_end_dt = datetime.combine(record_data.date, record_data.work_end)
        
        # Handle overnight shifts
        if work_end_dt < work_start_dt:
            work_end_dt = work_end_dt.replace(day=work_end_dt.day + 1)
        
        total_work_time = work_end_dt - work_start_dt
        total_hours = total_work_time.total_seconds() / 3600

        # Calculate mandatory break based on age and work hours
        if user.employee and hasattr(user.employee, 'age'):
            age = user.employee.age
        else:
            age = 18  # Default to adult if age not available

        if age < 18:
            break_minutes = 60
        else:
            if total_hours > 9:
                break_minutes = 45
            elif total_hours > 6:
                break_minutes = 30
            else:
                break_minutes = 0

        # Calculate net work hours and overtime
        net_hours = total_hours - (break_minutes / 60)
        overtime_hours = max(0, net_hours - record_data.expected_hours)

        # Create overtime record
        overtime_record = OvertimeRecord(
            user_id=user.id,
            date=record_data.date,
            work_start=record_data.work_start.isoformat(),
            work_end=record_data.work_end.isoformat(),
            break_minutes=break_minutes,
            worked_hours=round(net_hours, 2),
            expected_hours=record_data.expected_hours,
            overtime_hours=round(overtime_hours, 2),
        )

        return self.overtime_record_repository.create(overtime_record)

    def get_overtime_record_by_id(self, record_id: int) -> Optional[OvertimeRecord]:
        """Get an overtime record by ID."""
        return self.overtime_record_repository.get_by_id(record_id)

    def get_user_overtime_records(self, user_id: uuid.UUID) -> list[OvertimeRecord]:
        """Get all overtime records for a specific user."""
        return self.overtime_record_repository.get_by_user_id(user_id)

    def get_user_overtime_by_date_range(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[OvertimeRecord]:
        """Get overtime records for a user within a date range."""
        return self.overtime_record_repository.get_by_user_and_date_range(
            user_id, start_date, end_date
        )

    def get_all_overtime_records(self) -> list[OvertimeRecord]:
        """Get all overtime records (admin only)."""
        return self.overtime_record_repository.get_all()

    def update_overtime_record(
        self, record_id: int, update_data: OvertimeRecordUpdate, user: User
    ) -> Optional[OvertimeRecord]:
        """Update an existing overtime record."""
        record = self.overtime_record_repository.get_by_id(record_id)
        if not record:
            return None

        # Update fields if provided
        if update_data.date is not None:
            record.date = update_data.date
        
        # If work times are updated, recalculate everything
        if update_data.work_start is not None or update_data.work_end is not None:
            work_start = update_data.work_start or time.fromisoformat(record.work_start)
            work_end = update_data.work_end or time.fromisoformat(record.work_end)
            expected_hours = update_data.expected_hours or record.expected_hours

            # Recalculate with new times
            work_start_dt = datetime.combine(record.date, work_start)
            work_end_dt = datetime.combine(record.date, work_end)
            
            if work_end_dt < work_start_dt:
                work_end_dt = work_end_dt.replace(day=work_end_dt.day + 1)
            
            total_work_time = work_end_dt - work_start_dt
            total_hours = total_work_time.total_seconds() / 3600

            # Recalculate break
            age = user.employee.age if user.employee and hasattr(user.employee, 'age') else 18
            if age < 18:
                break_minutes = 60
            else:
                if total_hours > 9:
                    break_minutes = 45
                elif total_hours > 6:
                    break_minutes = 30
                else:
                    break_minutes = 0

            net_hours = total_hours - (break_minutes / 60)
            overtime_hours = max(0, net_hours - expected_hours)

            record.work_start = work_start.isoformat()
            record.work_end = work_end.isoformat()
            record.break_minutes = break_minutes
            record.worked_hours = round(net_hours, 2)
            record.expected_hours = expected_hours
            record.overtime_hours = round(overtime_hours, 2)
        elif update_data.expected_hours is not None:
            # Just update expected hours and recalculate overtime
            record.expected_hours = update_data.expected_hours
            record.overtime_hours = max(0, record.worked_hours - update_data.expected_hours)

        return self.overtime_record_repository.update(record)

    def delete_overtime_record(self, record_id: int) -> bool:
        """Delete an overtime record."""
        return self.overtime_record_repository.delete(record_id)

    def get_total_overtime(self, user_id: uuid.UUID) -> float:
        """Calculate total overtime hours for a user."""
        return self.overtime_record_repository.get_total_overtime_by_user(user_id)

