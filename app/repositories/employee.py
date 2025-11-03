import uuid
from typing import Optional

from sqlmodel import Session

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate


class EmployeeRepository:
    """Repository for Employee data access operations.

    Handles all database operations for Employee entities.
    Does NOT modify domain models or manage transactions.
    """

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLModel database session
        """
        self.session = session

    def create_employee(self, employee_in: EmployeeCreate) -> Employee:
        """Create a new employee entity (does not commit).

        Args:
            employee_in: Employee creation data

        Returns:
            Created Employee instance (not yet persisted)
        """
        employee = Employee(
            user_id=employee_in.user_id,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
        )
        self.session.add(employee)
        return employee

    def delete_employee(self, target: Employee) -> None:
        """Delete an employee (does not commit).

        Args:
            target: Employee to delete
        """
        self.session.delete(target)

    def get_employee_by_user_id(self, id: uuid.UUID) -> Optional[Employee]:
        return self.session.get(Employee, id)
