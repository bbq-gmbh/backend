import uuid

from pydantic import BaseModel
from typing import Optional

from .user import UserOnly, UserEmployeeOnly


class EmployeeCreate(BaseModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str


class EmployeeInfo(UserOnly):
    employee: UserEmployeeOnly


class HierarchyNode(BaseModel):
    """Represents a node in the employee hierarchy."""

    user_id: uuid.UUID
    username: str
    first_name: str
    last_name: str
    supervisor_id: Optional[uuid.UUID] = None
    depth: int


class HierarchyResponse(BaseModel):
    """Response containing hierarchy information for an employee."""

    employee: HierarchyNode
    supervisors: list[HierarchyNode]
    subordinates: list[HierarchyNode]


class HierarchyRebuildStats(BaseModel):
    """Statistics from a hierarchy rebuild operation."""

    records_deleted: int
    records_created: int
    employees_processed: int
    duration_seconds: float


class HierarchyRebuildResponse(BaseModel):
    """Response from hierarchy rebuild endpoint."""

    success: bool
    message: str
    stats: HierarchyRebuildStats
