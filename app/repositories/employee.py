import uuid
from typing import Optional

from app.models.employee import Employee
from app.repositories.user import UserRepository
from app.schemas.employee import EmployeeCreate


class EmployeeRepository:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.session = user_repo.session

    def create_employee(self, employee_in: EmployeeCreate) -> Employee:
        employee = Employee(
            user_id=employee_in.user_id,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
        )
        self.session.add(employee)
        return employee

    def delete_employee(self, target: Employee):
        self.session.delete(target)
    
    def get_employee_by_user_id(self, id: uuid.UUID) -> Optional[Employee]:
        return self.session.get(Employee, id)
