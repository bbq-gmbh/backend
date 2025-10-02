from sqlmodel import Session


class TimeRecordRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_time_record(self) -> None:
        pass

    def update_time_record(self) -> None:
        pass

    def delete_time_record(self) -> None:
        pass

    pass
