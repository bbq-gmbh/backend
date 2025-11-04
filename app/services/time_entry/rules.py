from app.models.time_entry import TimeEntry
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.time_entry import TimeEntryViolationReason


class TimeEntryRuleService:
    def __init__(self, time_entry_repo: TimeEntryRepository):
        self.time_entry_repo = time_entry_repo
        self.session = time_entry_repo.session

        self.rules = {
            ""
        }

    def rule_work_hours():
        pass