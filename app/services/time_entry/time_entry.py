from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import holidays

from app.config.settings import Settings
from app.core.datetime import (
    get_age,
    get_hours_between,
    get_years_between,
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
    ValidationError,
)
from app.models.absence_entry import AbsenceEntry, AbsenceEntryType
from app.models.time_entry import TimeEntry, TimeEntryType
from app.models.user import User
from app.repositories.absence_entry import AbsenceEntryRepository
from app.repositories.server_store import ServerStoreRepository
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.absence_entry import (
    AbsenceEntryCreate,
    AbsenceEntryDelete,
    AbsenceEntryGet,
)
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete, TimeEntryGet
from app.services.employee import EmployeeService


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

        time_entry_in.date_time = quantizise_minute(time_entry_in.date_time).replace(
            tzinfo=None
        )
        date_time = time_entry_in.date_time
        day = time_entry_in.date_time.date()

        server_store = self.server_store_repo.get()
        timezone = ZoneInfo(server_store.timezone)

        now_tz = datetime.now(tz=timezone).replace(tzinfo=None)
        now_tz_day = now_tz.date()

        if date_time > now_tz:
            raise DomainError("Creating time entries in the future is not allowed")

        if not force:
            day_diff = (now_tz_day - day).days
            if now_tz_day > day and day_diff > Settings.TIME_ENTRY_EDIT_MAX_DAYS:
                raise DomainError(
                    f"Cannot create time entry after {day_diff} day(s) (max allowed: {Settings.TIME_ENTRY_EDIT_MAX_DAYS})"
                )

        day_entry_count = self.time_entry_repo.get_time_entry_count_for_day(
            employee.user_id, day
        )

        if day_entry_count >= Settings.TIME_ENTRY_MAX_ENTRIES_PER_DAY:
            raise DomainError(
                f"Limit of max {Settings.TIME_ENTRY_MAX_ENTRIES_PER_DAY} time entries each day reached"
            )

        all_holidays = holidays.country_holidays(
            country="DE", subdiv="BW", language="DE"
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
                    employee.user_id, (day - timedelta(days=1))
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
                employee.user_id, (day + timedelta(days=1))
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
            if not actor.employee or actor.employee.user_id != time_entry.user_id:
                raise UserNotAuthorizedError("BBBB")

        day = time_entry.date_time.date()

        server_store = self.server_store_repo.get()
        timezone = ZoneInfo(server_store.timezone)

        now_tz = datetime.now(tz=timezone)
        now_tz_day = now_tz.date()

        if not force:
            day_diff = (now_tz_day - day).days
            if now_tz_day > day and day_diff > Settings.TIME_ENTRY_EDIT_MAX_DAYS:
                raise DomainError(
                    f"Cannot modify time entry after {day_diff} day(s) (max allowed: {Settings.TIME_ENTRY_EDIT_MAX_DAYS})"
                )

        self.time_entry_repo.delete_time_entry(time_entry)
        self.session.commit()

    def create_absence_entry(
        self,
        actor: User,
        absence_entry_in: AbsenceEntryCreate,
        *,
        force: bool = False,
        dry: bool = False,
    ) -> AbsenceEntry:
        if not actor.is_superuser and force:
            raise UserNotAuthorizedError()

        if not force:
            if not actor.employee or actor.employee.user_id != absence_entry_in.user_id:
                raise UserNotAuthorizedError()

        if not force and absence_entry_in.entry_type == AbsenceEntryType.Other:
            raise UserNotAuthorizedError()

        day_begin = absence_entry_in.date_begin
        day_end = absence_entry_in.date_end
        _days = (day_end - day_begin).days + 1

        if day_begin > day_end:
            raise ValidationError("date_begin is after date_end")

        server_store = self.server_store_repo.get()
        timezone = ZoneInfo(server_store.timezone)

        now_tz = datetime.now(tz=timezone)
        now_tz_day = now_tz.date()

        if not force:
            day_diff = (now_tz_day - day_begin).days
            if now_tz_day > day_begin and day_diff > Settings.TIME_ENTRY_EDIT_MAX_DAYS:
                raise DomainError(
                    f"Cannot create absence entry after {day_diff} day(s) (max allowed: {Settings.TIME_ENTRY_EDIT_MAX_DAYS})"
                )

        if not force and absence_entry_in.entry_type == AbsenceEntryType.Vacation:
            if now_tz_day >= day_begin:
                raise DomainError(
                    "Cannot create absence entry (vacation) for same or past day"
                )

        if not force and absence_entry_in.entry_type == AbsenceEntryType.Vacation:
            # TODO: check how many vacation days are left
            pass

        absence_entry = self.absence_entry_repo.create_absence_entry(
            actor, absence_entry_in
        )
        if not dry:
            self.session.commit()
            self.session.refresh(absence_entry)

        return absence_entry

    def delete_absence_entry(
        self,
        actor: User,
        absence_entry_delete: AbsenceEntryDelete,
        *,
        force: bool = False,
    ) -> None:
        if not actor.is_superuser and force:
            raise UserNotAuthorizedError()

        absence_entry = self.absence_entry_repo.get_abcence_entry_by_id(
            absence_entry_delete.id
        )

        if not absence_entry:
            raise ResourceNotFoundError()

        if not force:
            if not actor.employee or actor.employee.user_id != absence_entry.user_id:
                raise UserNotAuthorizedError()

        if not force and absence_entry.entry_type == AbsenceEntryType.Other:
            raise UserNotAuthorizedError()

        day = absence_entry.date_begin

        server_store = self.server_store_repo.get()
        timezone = ZoneInfo(server_store.timezone)

        now_tz = datetime.now(tz=timezone)
        now_tz_day = now_tz.date()

        if not force:
            day_diff = (now_tz_day - day).days
            if now_tz_day > day and day_diff > Settings.TIME_ENTRY_EDIT_MAX_DAYS:
                raise DomainError(
                    f"Cannot modify absence entry after {day_diff} day(s) (max allowed: {Settings.TIME_ENTRY_EDIT_MAX_DAYS})"
                )

        if not force and absence_entry.entry_type == AbsenceEntryType.Vacation:
            if now_tz_day >= day:
                raise DomainError(
                    "Cannot modify absence entry (vacation) on same or past this day"
                )

        self.absence_entry_repo.delete_absence_entry(absence_entry)
        self.session.commit()

    @staticmethod
    def _extract_absence_entries(
        entries, date_begin: date, date_end: date
    ) -> list[None | tuple[AbsenceEntryType, AbsenceEntry]]:
        if date_begin > date_end:
            raise ValueError("date_begin > date_end")

        day_count = (date_end - date_begin).days + 1
        arr: list[None | tuple[AbsenceEntryType, AbsenceEntry]] = [
            None for _ in range(day_count)
        ]

        for entry in entries:
            entry: AbsenceEntry

            if entry.date_end < date_begin or entry.date_begin > date_end:
                continue

            for i in range(
                (entry.date_begin - date_begin).days,
                (entry.date_end - date_begin).days + 1,
            ):
                v = arr[i]
                if v is not None:
                    v1, _ = v
                    if (
                        v1 == entry.entry_type
                        or v1 == AbsenceEntryType.Other
                        or v1 == AbsenceEntryType.Sickness
                    ):
                        continue
                    arr[i] = entry.entry_type, entry
                else:
                    arr[i] = entry.entry_type, entry

        return arr

    @staticmethod
    def _extract_absence_entries_apply_holidays(
        arr: list[None | tuple[AbsenceEntryType, AbsenceEntry]],
        date_begin: date,
        holidays: holidays.HolidayBase,
    ) -> list[None | tuple[AbsenceEntryType, AbsenceEntry]]:
        ret: list[None | tuple[AbsenceEntryType, AbsenceEntry]] = [
            None for _ in range(len(arr))
        ]
        for i, x in enumerate(arr):
            day = date_begin + timedelta(days=i)
            if x is not None and day in holidays:
                continue
            ret[i] = x
        return ret

    @staticmethod
    def _extract_absence_entries_apply_workdays(
        arr: list[None | tuple[AbsenceEntryType, AbsenceEntry]],
        date_begin: date,
    ) -> list[None | tuple[AbsenceEntryType, AbsenceEntry]]:
        ret: list[None | tuple[AbsenceEntryType, AbsenceEntry]] = [
            None for _ in range(len(arr))
        ]
        for i, x in enumerate(arr):
            day = date_begin + timedelta(days=i)
            if x is not None and (
                not is_workday(day) or day.weekday() not in [0, 1, 2, 3, 4]
            ):
                continue
            ret[i] = x
        return ret

    @staticmethod
    def _extract_holidays_from_extracted_absence_entries(
        arr: list[None | tuple[AbsenceEntryType, AbsenceEntry]],
    ) -> int:
        return sum(
            1 for x in arr if x is not None and x[0] == AbsenceEntryType.Vacation
        )

    @staticmethod
    def _extract_sick_days_from_extracted_absence_entries(
        arr: list[None | tuple[AbsenceEntryType, AbsenceEntry]],
    ) -> int:
        return sum(
            1 for x in arr if x is not None and x[0] == AbsenceEntryType.Vacation
        )

    def get_time_entries(
        self,
        employee_service: EmployeeService,
        actor: User,
        time_entry_get: TimeEntryGet,
    ) -> Optional[TimeEntry] | list[TimeEntry]:
        employee = self.employee_repo.get_employee_by_user_id(time_entry_get.user_id)

        if not employee:
            raise EmployeeNotFoundError(user_id=time_entry_get.user_id)

        if not actor.is_superuser:
            if not actor.employee:
                raise UserNotAuthorizedError()
            if not employee_service.is_supervisor_of(
                actor.employee, employee, include_self=True
            ):
                raise UserNotAuthorizedError()

        if time_entry_get.id is not None:
            return self.time_entry_repo.get_time_entry_by_id(time_entry_get.id)

        if time_entry_get.date is not None:
            return self.time_entry_repo.get_time_entries_for_day(
                employee.user_id, time_entry_get.date
            )

        if time_entry_get.from_date is not None and time_entry_get.to_date:
            from_date, to_date = time_entry_get.from_date, time_entry_get.to_date
            if from_date > to_date:
                ValidationError("from_date is after to_date")
            if get_years_between(to_date, from_date) > 1.05:
                ValidationError("Maximum date span can be 1 year")

            return self.time_entry_repo.get_time_entries_in_range(
                employee.user_id, from_date, to_date
            )

        raise ValidationError(
            "TimeEntryGet requires either id, date or from_date & to_date"
        )

    def get_absence_entries(
        self,
        employee_service: EmployeeService,
        actor: User,
        absence_entry_get: AbsenceEntryGet,
    ) -> Optional[AbsenceEntry] | list[AbsenceEntry]:
        employee = self.employee_repo.get_employee_by_user_id(absence_entry_get.user_id)

        if not employee:
            raise EmployeeNotFoundError(user_id=absence_entry_get.user_id)

        if not actor.is_superuser:
            if not actor.employee:
                raise UserNotAuthorizedError()
            if not employee_service.is_supervisor_of(
                actor.employee, employee, include_self=True
            ):
                raise UserNotAuthorizedError()

        if absence_entry_get.id is not None:
            return self.absence_entry_repo.get_abcence_entry_by_id(absence_entry_get.id)

        if absence_entry_get.date is not None:
            return self.absence_entry_repo.get_all_entries_for_day(
                employee.user_id, absence_entry_get.date
            )

        if absence_entry_get.from_date is not None and absence_entry_get.to_date:
            from_date, to_date = absence_entry_get.from_date, absence_entry_get.to_date
            if from_date > to_date:
                ValidationError("from_date is after to_date")
            if get_years_between(to_date, from_date) > 1.05:
                ValidationError("Maximum date span can be 1 year")

            return self.absence_entry_repo.get_all_entries_in_range(
                employee.user_id, from_date, to_date
            )

        raise ValidationError(
            "AbsenceEntryGet requires either id, date or from_date & to_date"
        )
