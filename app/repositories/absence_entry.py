from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import select

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
            date_begin=absence_entry_in.date_begin,
            date_end=absence_entry_in.date_end,
            created_by=author.id,
            created_at=now,
            last_updated=now,
        )
        self.session.add(time_entry)
        return time_entry

    def get_abcence_entry_by_id(self, id: int) -> Optional[AbsenceEntry]:
        return self.session.get(AbsenceEntry, id)

    def get_all_entries_for_day(self, day: date) -> list[AbsenceEntry]:
        exec = select(AbsenceEntry).where(
            AbsenceEntry.date_begin >= day, AbsenceEntry.date_end <= day
        )
        return list(self.session.scalars(exec).all())
