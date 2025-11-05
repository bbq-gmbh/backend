import uuid

from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import func, select, or_

from app.core.datetime import get_day_times
from app.models.time_entry import TimeEntry, TimeEntryType
from app.models.user import User
from app.repositories.employee import EmployeeRepository
from app.schemas.time_entry import TimeEntryCreate


class TimeEntryRepository:
    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo
        self.session = employee_repo.session

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
        )
        self.session.add(time_entry)
        return time_entry

    def delete_time_entry(self, time_entry: TimeEntry) -> None:
        self.session.delete(time_entry)

    def get_time_entry_by_id(self, id: int) -> Optional[TimeEntry]:
        return self.session.get(TimeEntry, id)

    def get_time_entries_for_day(
        self, user_id: uuid.UUID, day: date
    ) -> list[TimeEntry]:
        mi, ma = get_day_times(day)

        exec = (
            select(TimeEntry)
            .where(TimeEntry.user_id == user_id)
            .where(TimeEntry.date_time >= mi, TimeEntry.date_time <= ma)
            .order_by(TimeEntry.date_time.asc())  # type: ignore
        )

        return list(self.session.scalars(exec).all())

    def get_time_entry_count_for_day(self, user_id: uuid.UUID, day: date) -> int:
        mi, ma = get_day_times(day)

        exec = select(func.count()).select_from(
            select(TimeEntry)
            .where(TimeEntry.user_id == user_id)
            .where(TimeEntry.date_time >= mi, TimeEntry.date_time <= ma)
            .order_by(TimeEntry.date_time.asc())  # type: ignore
        )

        return self.session.scalar(exec) or 0

    def get_last_departure_entry_for_day(
        self, user_id: uuid.UUID, day: date
    ) -> Optional[TimeEntry]:
        mi, ma = get_day_times(day)

        exec = (
            select(TimeEntry)
            .where(TimeEntry.user_id == user_id)
            .where(TimeEntry.date_time >= mi, TimeEntry.date_time <= ma)
            .where(TimeEntry.entry_type == TimeEntryType.Departure)
            .order_by(TimeEntry.date_time.desc())  # type: ignore
            .limit(1)
        )

        return self.session.scalar(exec)

    def get_first_arrival_entry_for_day(
        self, user_id: uuid.UUID, day: date
    ) -> Optional[TimeEntry]:
        mi, ma = get_day_times(day)

        exec = (
            select(TimeEntry)
            .where(TimeEntry.user_id == user_id)
            .where(TimeEntry.date_time >= mi, TimeEntry.date_time <= ma)
            .where(TimeEntry.entry_type == TimeEntryType.Arrival)
            .order_by(TimeEntry.date_time.desc())  # type: ignore
            .limit(1)
        )

        return self.session.scalar(exec)

    def get_time_entries_in_range(
        self, user_id: uuid.UUID, date_begin: date, date_end: date
    ) -> list[TimeEntry]:
        mi, _ = get_day_times(date_begin)
        _, ma = get_day_times(date_end)

        exec = (
            select(TimeEntry)
            .where(TimeEntry.user_id == user_id)
            .where(TimeEntry.date_time >= mi, TimeEntry.date_time <= ma)
            .order_by(TimeEntry.date_time.asc())  # type: ignore
        )

        return list(self.session.scalars(exec).all())
