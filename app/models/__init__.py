"""
Models package.

Import all SQLModel models here to ensure they are registered
with SQLModel.metadata before database initialization.
"""

from app.models.employee import Employee
from app.models.employee_hierarchy import EmployeeHierarchy
from app.models.user import User
from app.models.time_entry import TimeEntry

__all__ = ["User", "Employee", "EmployeeHierarchy", "TimeEntry"]
