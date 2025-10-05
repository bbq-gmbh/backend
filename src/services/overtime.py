from sqlmodel import Session

from src.models.user import User
from src.repositories.overtime import OvertimeRecord
from datetime import datetime

class TimeRecordService:
    def __init__(self, overtime_record_repository: OvertimeRecord) -> None:
        self.overtime_record_repository = overtime_record_repository
        self._session: Session = OvertimeRecord.session

    def create_overtime_record(
        self,
        user: User,
        work_start: datetime,
        work_end: datetime,
        expected_hours: float = 8.0
    ) -> OvertimeRecord:
        """Creates an overtime record for a user based on their work times and breaks.
         Args:
            user (User): The user for whom the overtime record is being created.    
            work_start (datetime): The start time of the work period.
            work_end (datetime): The end time of the work period.
            expected_hours (float): The expected core work hours for the day. Default is 8.0 hours.
            Returns:
            OvertimeRecord: The created overtime record.
        """

        # 1. Arbeitszeit berechnen
        total_work_time = work_end - work_start
        total_hours = total_work_time.total_seconds() / 3600

        # 2. Pausenregel anwenden
        if user.age < 18:
            break_minutes = 60
        else:
            if total_hours > 9:
                break_minutes = 45
            elif total_hours > 6:
                break_minutes = 30
            else:
                break_minutes = 0

        net_hours = total_hours - (break_minutes / 60)

        # 3. Überstunden berechnen
        overtime_hours = max(0, net_hours - expected_hours)

        # 4. OvertimeRecord speichern
        overtime_record = OvertimeRecord(
            user_id=user.id,
            date=work_start.date(),
            worked_hours=net_hours,
            overtime_hours=overtime_hours,
        )

        self.overtime_record_repository.save(self._session, overtime_record)
        return overtime_record
