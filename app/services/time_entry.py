from app.core.exceptions import ResourceNotFoundError, UserNotAuthorizedError
from app.models.employee import Employee
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete, TimeEntryUpdate


class TimeEntryService:
    def __init__(self, *, time_entry_repo: TimeEntryRepository):
        self.time_entry_repo = time_entry_repo
        self.employee_repo = time_entry_repo.employee_repo
        self.user_repo = self.employee_repo.user_repo
        self.session = self.user_repo.session

    def create_time_entry(
        self, actor: User, time_entry_in: TimeEntryCreate
    ) -> TimeEntry:
        if actor.employee is None:  # We are not employee
            if not actor.is_superuser:  # We are also not superuser
                raise UserNotAuthorizedError()
        else:  # We are employee
            if actor.is_superuser:  # We are superuser
                pass
            elif actor.id == time_entry_in.user_id:  # Ids match
                pass
            else:  # Ids don't match and we are not superuser
                raise UserNotAuthorizedError()

        # TODO: check if this time entry is allowed to be made

        time_entry = self.time_entry_repo.create_time_entry(actor, time_entry_in)

        self.session.commit()
        self.session.refresh(time_entry)

        return time_entry

    def update_time_entry(
        self, actor: User, time_entry_update: TimeEntryUpdate
    ) -> TimeEntry:
        if actor.employee is None:  # We are not employee
            if not actor.is_superuser:  # We are also not superuser
                raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.get_time_entry_by_id(time_entry_update.id)

        if time_entry is None:
            raise ResourceNotFoundError()

        if actor.is_superuser:  # Okay if superuser
            pass
        elif actor.employee:  # Employee
            if (
                actor.employee.user_id != time_entry.user_id
            ):  # Employee doesn't match time entry
                raise UserNotAuthorizedError()
        else:  # Not superuser and not employee
            raise UserNotAuthorizedError()

        # TODO: check if the updated time entry is allowed to be made

        time_entry.date_time = time_entry_update.date_time

        self.session.add(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)

        return time_entry

    def delete_time_entry(self, actor: User, time_entry_delete: TimeEntryDelete):
        # TODO: checks
        if actor.employee is None:  # We are not employee
            if not actor.is_superuser:  # We are also not superuser
                raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.get_time_entry_by_id(time_entry_delete.id)

        if time_entry is None:
            raise ResourceNotFoundError()

        if actor.is_superuser:  # Okay if superuser
            pass
        elif actor.employee:  # Employee
            if (
                actor.employee.user_id != time_entry.user_id
            ):  # Employee doesn't match time entry
                raise UserNotAuthorizedError()
        else:  # Not superuser and not employee
            raise UserNotAuthorizedError()

        # TODO: check if we are allowed to delete the time entry

        self.session.delete(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)

        return
