from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import holidays

from app.config.settings import Settings
from app.core.datetime import (
    get_age,
    get_hours_between,
    is_in_work_hours,
    is_in_work_hours_underage,
    is_workday,
    quantizise_minute,
)
from app.core.exceptions import (
    DomainError,
    EmployeeNotFoundError,
    ResourceNotFoundError,
    UserNotAuthorizedError,
)
from app.models.absence_entry import AbsenceEntry
from app.models.time_entry import TimeEntry, TimeEntryType
from app.models.user import User
from app.repositories.absence_entry import AbsenceEntryRepository
from app.repositories.server_store import ServerStoreRepository
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.absence_entry import AbsenceEntryCreate
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete

from .rules import TimeEntryRuleService


class TimeEntryService:
    def __init__(
        self,
        *,
        time_entry_repo: TimeEntryRepository,
        absence_entry_repo: AbsenceEntryRepository,
        server_store_repo: ServerStoreRepository,
    ):
        self.time_entry_repo = time_entry_repo
        self.absence_entry_repo = absence_entry_repo
        self.server_store_repo = server_store_repo

        self.employee_repo = time_entry_repo.employee_repo
        self.session = self.employee_repo.session

        self.rule_service = TimeEntryRuleService(time_entry_repo)

    def create_time_entry(
        self, actor: User, time_entry_in: TimeEntryCreate, *, force: bool = False
    ) -> TimeEntry:
        if not actor.is_superuser and force:
            raise UserNotAuthorizedError()

        if not force:
            if not actor.employee or actor.employee.user_id != time_entry_in.user_id:
                raise UserNotAuthorizedError()

        employee = self.employee_repo.get_employee_by_user_id(time_entry_in.user_id)

        if not employee:
            raise EmployeeNotFoundError(user_id=time_entry_in.user_id)

        time_entry_in.date_time = quantizise_minute(time_entry_in.date_time)
        date_time = time_entry_in.date_time
        day = time_entry_in.date_time.date()

        server_store = self.server_store_repo.get()
        timezone = ZoneInfo(server_store.timezone)

        now_tz = datetime.now(tz=timezone).replace(tzinfo=None)

        if day > now_tz:
            raise DomainError("Creating time entries in the future is not allowed")

        day_entry_count = self.time_entry_repo.get_time_entry_count_for_day(day)

        if day_entry_count >= Settings.TIME_ENTRY_MAX_ENTRIES_PER_DAY:
            raise DomainError(
                f"Limit of max {Settings.TIME_ENTRY_MAX_ENTRIES_PER_DAY} time entries each day reached"
            )

        time_config = self.time_entry_repo.get_time_config_for_day(day)

        if not time_config:
            raise DomainError("Time config does not exist for this date")

        all_holidays = holidays.country_holidays(
            country="DE", subdiv=time_config.holidays_region, language="DE"
        )
        day_holiday = all_holidays.get(day)

        if not force and day_holiday:
            raise DomainError(f"Time entry violates holiday: {day_holiday}")

        employee_age = get_age(employee.birthday, day)
        employee_underage = employee_age < 18

        if not force:
            if not is_workday(day):
                raise DomainError("Time entry is outside workdays")

        if not force:
            if not is_in_work_hours(date_time.time()):
                raise DomainError("Time entry is in rest period")

            if employee_underage and not is_in_work_hours_underage(date_time.time()):
                raise DomainError("Time entry is in rest period (underage rules)")

        if not force and time_entry_in.entry_type == TimeEntryType.Arrival:
            departure_entry_before = (
                self.time_entry_repo.get_last_departure_entry_for_day(
                    (day - timedelta(days=1))
                )
            )

            if departure_entry_before:
                if get_hours_between(date_time, departure_entry_before.date_time) < 11:
                    raise DomainError("Arrival entry violates rest hours")

                if (
                    employee_underage
                    and get_hours_between(date_time, departure_entry_before.date_time)
                    < 12
                ):
                    raise DomainError(
                        "Arrival entry violates rest hours (underage rules)"
                    )

        if not force and time_entry_in.entry_type == TimeEntryType.Departure:
            arrival_entry_after = self.time_entry_repo.get_first_arrival_entry_for_day(
                (day + timedelta(days=1))
            )

            if arrival_entry_after:
                if get_hours_between(arrival_entry_after.date_time, date_time) < 11:
                    raise DomainError("Departure entry violates rest hours")

                if (
                    employee_underage
                    and get_hours_between(arrival_entry_after.date_time, date_time) < 12
                ):
                    raise DomainError(
                        "Departure entry violates rest hours (underage rules)"
                    )

        time_entry = self.time_entry_repo.create_time_entry(actor, time_entry_in)
        self.session.commit()
        self.session.refresh(time_entry)

        return time_entry

    def delete_time_entry(
        self, actor: User, time_entry_delete: TimeEntryDelete, *, force: bool = False
    ):
        if not actor.is_superuser and force:
            raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.get_time_entry_by_id(time_entry_delete.id)

        if not time_entry:
            raise ResourceNotFoundError()

        if not force:
            if not actor.employee or actor.employee.user_id != time_entry.id:
                raise UserNotAuthorizedError()

        day = time_entry.date_time.date()

        server_store = self.server_store_repo.get()
        timezone = ZoneInfo(server_store.timezone)

        now_tz = datetime.now(tz=timezone)
        now_tz_day = now_tz.date()

        if not force and actor.employee:
            day_diff = (now_tz_day - day).days
            if now_tz_day > day and day_diff > Settings.TIME_ENTRY_EDIT_MAX_DAYS:
                raise DomainError(
                    f"Cannot modify the time entry after {day_diff} day(s) (max allowed: {Settings.TIME_ENTRY_EDIT_MAX_DAYS})"
                )

        self.time_entry_repo.delete_time_entry(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)

    def create_absence_entry(
        self,
        actor: User,
        absence_entry_create: AbsenceEntryCreate,
        *,
        force: bool = False,
    ) -> AbsenceEntry:
        if not actor.is_superuser and force:
            raise UserNotAuthorizedError()

        if not force:
            if (
                not actor.employee
                or actor.employee.user_id != absence_entry_create.user_id
            ):
                raise UserNotAuthorizedError()

        absence_entry = self.absence_entry_repo.create_absence_entry(
            actor, absence_entry_create
        )
        self.session.commit()
        self.session.refresh(absence_entry)

        return absence_entry
