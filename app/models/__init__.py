"""
Models package.

Import all SQLModel models here to ensure they are registered
with SQLModel.metadata before database initialization.
"""

from app.models.server_store import ServerStore
from app.models.employee import Employee
from app.models.employee_hierarchy import EmployeeHierarchy
from app.models.user import User
from app.models.time_entry import TimeEntry
from app.models.absence_entry import AbsenceEntry
from app.models.employee_time_config import EmployeeTimeConfig

__all__ = [
    "ServerStore",
    "User",
    "Employee",
    "EmployeeHierarchy",
    "TimeEntry",
    "AbsenceEntry",
    "EmployeeTimeConfig",
]
