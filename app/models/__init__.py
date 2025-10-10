"""
Models package.

Import all SQLModel models here to ensure they are registered
with SQLModel.metadata before database initialization.
"""

from app.models.employee import Employee
from app.models.user import User

__all__ = ["User", "Employee"]
