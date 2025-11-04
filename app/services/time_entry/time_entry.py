from datetime import datetime
from zoneinfo import ZoneInfo

import holidays

from app.config.settings import Settings
from app.core.datetime import quantizise_minute
from app.core.exceptions import (
    DomainError,
    ResourceNotFoundError,
    UserNotAuthorizedError,
)
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.repositories.absence_entry import AbsenceEntryRepository
from app.repositories.server_store import ServerStoreRepository
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete, TimeEntryUpdate

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

        time_entry_in.date_time = quantizise_minute(time_entry_in.date_time)
        day = time_entry_in.date_time.date()

        server_store = self.server_store_repo.get()
        timezone = ZoneInfo(server_store.timezone)

        now_tz = datetime.now(tz=timezone)

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

        if day_holiday:
            raise DomainError(f"Time entry violates holiday: {day_holiday}")

        # TODO

        return None  # type: ignore

    def update_time_entry(
        self, actor: User, time_entry_update: TimeEntryUpdate, *, force: bool = False
    ) -> TimeEntry:
        return None  # type: ignore

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
