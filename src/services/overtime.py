from sqlmodel import Session

from src.models.user import User
from src.repositories.overtime import OvertimeRecord


class TimeRecordService:
    def __init__(self, overtime_record_repository: OvertimeRecord) -> None :
        self.overtime_record_repository = overtime_record_repository
        self._session: Session = OvertimeRecord.session

    def create_overtime_record(self, user: User) -> None:
        self.create_overtime_record.create_overtime
