from datetime import datetime, timezone
from typing import Optional
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.repositories.employee import EmployeeRepository
from app.schemas.time_entry import TimeEntryCreate


class TimeEntryRepository:
    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo
        self.user_repo = employee_repo.user_repo
        self.session = self.user_repo.session

    def create_time_entry(
        self, author: User, time_entry_in: TimeEntryCreate
    ) -> TimeEntry:
        now = datetime.now(timezone.utc)
        time_entry = TimeEntry(
            user_id=time_entry_in.user_id,
            entry_type=time_entry_in.entry_type,
            date_time=time_entry_in.date_time,
            created_by=author.id,
            created_at=now,
            last_updated=now,
        )
        self.session.add(time_entry)
        return time_entry

    def get_time_entry_by_id(self, id: int) -> Optional[TimeEntry]:
        return self.session.get(TimeEntry, id)
