from app.core.exceptions import (
    EmployeeNotFoundError,
    ResourceNotFoundError,
    UserNotAuthorizedError,
)
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.repositories.time_entry import TimeEntryRepository
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete, TimeEntryUpdate


class TimeEntryService:
    def __init__(self, *, time_entry_repo: TimeEntryRepository):
        self.time_entry_repo = time_entry_repo
        self.employee_repo = time_entry_repo.employee_repo
        self.session = self.employee_repo.session

    def create_time_entry(
        self, actor: User, time_entry_in: TimeEntryCreate
    ) -> TimeEntry:
        if actor.employee is None:
            if not actor.is_superuser:
                raise UserNotAuthorizedError()
        else:
            if actor.is_superuser:
                pass
            elif actor.id == time_entry_in.user_id:
                pass
            else:
                raise UserNotAuthorizedError()

        target_employee = self.employee_repo.get_employee_by_user_id(
            time_entry_in.user_id
        )

        if not target_employee:
            raise EmployeeNotFoundError(user_id=time_entry_in.user_id)

        # TODO: check if this time entry is allowed to be made

        time_entry = self.time_entry_repo.create_time_entry(actor, time_entry_in)

        self.session.commit()
        self.session.refresh(time_entry)

        return time_entry

    def update_time_entry(
        self, actor: User, time_entry_update: TimeEntryUpdate
    ) -> TimeEntry:
        if actor.employee is None:
            if not actor.is_superuser:
                raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.get_time_entry_by_id(time_entry_update.id)

        if time_entry is None:
            raise ResourceNotFoundError()

        if actor.is_superuser:
            pass
        elif actor.employee:
            if actor.employee.user_id != time_entry.user_id:
                raise UserNotAuthorizedError()
        else:
            raise UserNotAuthorizedError()

        # TODO: check if the updated time entry is allowed to be made

        time_entry.date_time = time_entry_update.date_time

        self.session.add(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)

        return time_entry

    def delete_time_entry(self, actor: User, time_entry_delete: TimeEntryDelete):
        # TODO: checks
        if actor.employee is None:
            if not actor.is_superuser:
                raise UserNotAuthorizedError()

        time_entry = self.time_entry_repo.get_time_entry_by_id(time_entry_delete.id)

        if time_entry is None:
            raise ResourceNotFoundError()

        if actor.is_superuser:
            pass
        elif actor.employee:
            if actor.employee.user_id != time_entry.user_id:
                raise UserNotAuthorizedError()
        else:
            raise UserNotAuthorizedError()

        # TODO: check if we are allowed to delete the time entry

        self.session.delete(time_entry)
        self.session.commit()
        self.session.refresh(time_entry)

        return
