from app.core.datetime import quantizise_minute
from app.core.exceptions import (
    UserNotAuthorizedError,
)
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete, TimeEntryUpdate

from .rules import TimeEntryRuleService


class TimeEntryService:
    def __init__(self, *, time_entry_repo: TimeEntryRepository):
        self.time_entry_repo = time_entry_repo
        self.employee_repo = time_entry_repo.employee_repo
        self.session = self.employee_repo.session

        self.rule_service = TimeEntryRuleService(time_entry_repo)

    def create_time_entry(
        self, actor: User, time_entry_in: TimeEntryCreate
    ) -> TimeEntry:
        if not actor.is_superuser:
            if not actor.employee or actor.employee.user_id != time_entry_in.user_id:
                raise UserNotAuthorizedError()

        time_entry_in.date_time = quantizise_minute(time_entry_in.date_time)

        return None  # type: ignore

    def update_time_entry(
        self, actor: User, time_entry_update: TimeEntryUpdate
    ) -> TimeEntry:
        return None  # type: ignore

    def delete_time_entry(self, actor: User, time_entry_delete: TimeEntryDelete):
        return None  # type: ignore
