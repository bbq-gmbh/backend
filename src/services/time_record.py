from sqlmodel import Session

from src.models.user import User
from src.repositories.time_record import TimeRecordRepository


class TimeRecordService:
    def __init__(self, time_record_repository: TimeRecordRepository):
        self.time_record_repository = time_record_repository
        self._session: Session = time_record_repository.session

    def create_time_record(self, user: User) -> None:
        self.time_record_repository.create_time_record()
        pass
