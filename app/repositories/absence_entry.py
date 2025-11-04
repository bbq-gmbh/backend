from datetime import datetime, timezone

from app.models.absence_entry import AbsenceEntry
from app.models.user import User
from app.repositories.employee import EmployeeRepository
from app.schemas.absence_entry import AbsenceEntryCreate


class AbsenceEntryRepository:
    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo
        self.session = employee_repo.session

    def create_absence_entry(
        self, author: User, absence_entry_in: AbsenceEntryCreate
    ) -> AbsenceEntry:
        now = datetime.now(timezone.utc)
        time_entry = AbsenceEntry(
            user_id=absence_entry_in.user_id,
            entry_type=absence_entry_in.entry_type,
            date_start=absence_entry_in.date_start,
            date_end=absence_entry_in.date_end,
            created_by=author.id,
            created_at=now,
            last_updated=now,
        )
        self.session.add(time_entry)
        return time_entry
