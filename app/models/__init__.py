"""
Models package.

Import all SQLModel models here to ensure they are registered
with SQLModel.metadata before database initialization.
"""

from app.models.absence_entry import AbsenceEntry
from app.models.employee_hierarchy import EmployeeHierarchy
from app.models.employee_time_config import EmployeeTimeConfig
from app.models.employee import Employee
from app.models.server_store import ServerStore
from app.models.time_entry import TimeEntry
from app.models.user import User

__all__ = [
    "AbsenceEntry",
    "EmployeeHierarchy",
    "EmployeeTimeConfig",
    "Employee",
    "ServerStore",
    "TimeEntry",
    "User",
]
