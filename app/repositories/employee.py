from app.models.employee import Employee
from app.repositories.user import UserRepository
from app.schemas.employee import EmployeeCreate


class EmployeeRepository:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.session = user_repository.session

    def create_employee(self, employee_in: EmployeeCreate) -> Employee:
        employee = Employee(
            user_id=employee_in.user_id,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
        )
        self.session.add(employee)
        return employee
