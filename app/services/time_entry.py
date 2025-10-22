from app.core.exceptions import ResourceNotFoundError, UserNotAuthorizedError
from app.models.employee import Employee
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete, TimeEntryUpdate


class TimeEntryService:
    def __init__(self, time_entry_repo: TimeEntryRepository):
        self.time_entry_repo = time_entry_repo
        self.employee_repo = time_entry_repo.employee_repo
        self.user_repo = self.employee_repo.user_repo
        self.session = self.user_repo.session

    def create_time_entry(
        self, actor: User, time_entry_in: TimeEntryCreate
    ) -> TimeEntry:
        # TODO: checks

        if not actor.is_superuser and (
            actor.employee is None or actor.employee.user_id != time_entry_in.user_id
        ):
            raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.create_time_entry(actor, time_entry_in)

        self.session.commit()
        self.session.refresh(time_entry)

        return time_entry

    def update_time_entry(
        self, actor: User, time_entry_update: TimeEntryUpdate
    ) -> TimeEntry:
        # TODO: checks

        if not actor.is_superuser and actor.employee is None:
            raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.get_time_entry(time_entry_update.id)

        if time_entry is None:
            raise ResourceNotFoundError()
        if not actor.is_superuser and actor.employee.user_id != time_entry.user_id:
            raise UserNotAuthorizedError()

        time_entry.date_time = time_entry_update.date_time

        self.session.add(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)

        return time_entry

    def delete_time_entry(self, actor: User, time_entry_delete: TimeEntryDelete):
        # TODO: checks

        if not actor.is_superuser and actor.employee is None:
            raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.get_time_entry(time_entry_delete.id)

        if time_entry is None:
            raise ResourceNotFoundError()
        if not actor.is_superuser and actor.employee.user_id != time_entry.user_id:
            raise UserNotAuthorizedError()

        # TODO: CHECKS!!

        self.session.delete(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)

        return
