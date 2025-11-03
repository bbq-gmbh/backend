# Employee Hierarchy Production Specification

## 🚨 Executive Summary

**Current Status:** The employee hierarchy system has a working closure table implementation BUT suffers from serious architectural issues that must be fixed before adding new features.

**Main Issues:**
1. 🔴 **Broken Separation of Concerns** - Repositories modify domain models, services manage transactions
2. 🔴 **Session Management Chaos** - `session.commit()` scattered across multiple layers
3. 🔴 **Tangled Dependencies** - Services reach through repositories (`employee_repo.user_repo.session`)
4. 🔴 **No Transaction Boundaries** - Operations can partially fail with data inconsistency
5. 🔴 **Missing Functionality** - No rebuild, validation, or recovery mechanisms

**Required Action:**
1. **FIRST:** Refactor architecture (2-3 weeks) - See "Phase 0: Architectural Refactoring"
2. **THEN:** Add production features (rebuild, validation, etc.)

**DO NOT SKIP PHASE 0!** Adding features on the current architecture will create unmaintainable technical debt.

---

## Overview
This document outlines the additional functionality required for the employee hierarchy system to be production-ready. The current implementation uses a closure table pattern (`EmployeeHierarchy`) to efficiently track ancestor-descendant relationships.

**CRITICAL:** This spec also addresses significant architectural issues in the current implementation that must be fixed before adding new features.

## Current State Analysis

### Existing Functionality
- ✅ Basic hierarchy operations (assign/remove supervisor)
- ✅ Query subordinates and supervisors
- ✅ Hierarchy level comparison methods
- ✅ Closure table for efficient queries

### Gaps Identified - Functionality
- ❌ No hierarchy rebuild mechanism
- ❌ No validation/integrity checks
- ❌ No bulk operations
- ❌ Limited debugging/diagnostic tools
- ❌ No orphan detection/handling
- ❌ No cycle detection
- ❌ No hierarchy depth validation

### Critical Architectural Issues ⚠️

#### 1. **Violation of Repository Pattern**
- **Issue:** Repositories are modifying domain models directly (e.g., `target.supervisor = None` in `EmployeeHierarchyRepository.remove_supervisor()`)
- **Problem:** Repositories should only handle data persistence, not domain logic
- **Impact:** Tight coupling, difficult to test, breaks separation of concerns

#### 2. **Session Management Chaos**
- **Issue:** Session handling scattered across multiple layers:
  - Services call `self.session.commit()` and `self.session.add()`
  - Services access `self.session` via `self.user_repo.session`
  - No consistent transaction boundaries
- **Problem:** 
  - Transaction management is not centralized
  - Hard to track where commits happen
  - Difficult to implement proper rollback logic
  - Can't easily implement unit of work pattern
- **Impact:** Brittle error handling, hard to maintain consistency

#### 3. **Tangled Dependencies**
- **Issue:** Complex dependency chains:
  - `EmployeeRepository` depends on `UserRepository`
  - `EmployeeService` accesses `employee_repo.user_repo`
  - Session passed through multiple layers
- **Problem:** Hard to understand data flow, difficult to refactor
- **Impact:** Testing complexity, maintenance burden

#### 4. **Mixed Responsibilities in Service Layer**
- **Issue:** 
  - Services contain both business logic AND transaction management
  - Static methods in `EmployeeService` that traverse ORM relationships directly
  - Authorization logic using static service methods
- **Problem:** Services doing too much, unclear boundaries
- **Impact:** Hard to test, violates single responsibility principle

#### 5. **Inconsistent Error Handling**
- **Issue:** No consistent pattern for handling:
  - Constraint violations
  - Concurrent modifications
  - Database errors during hierarchy operations
- **Impact:** Potential data corruption, unpredictable behavior

#### 6. **Missing Transaction Boundaries**
- **Issue:** Operations like `assign_supervisor` and `remove_supervisor` don't ensure atomicity
- **Problem:** Partial updates possible if errors occur mid-operation
- **Impact:** Data inconsistency risk

#### 7. **No Clear Separation Between Read and Write Operations**
- **Issue:** Same repository methods used for queries and mutations
- **Problem:** Hard to optimize, cache, or scale independently
- **Impact:** Performance limitations, can't easily implement CQRS if needed

---

## Architectural Refactoring Plan 🏗️

### Phase 0: Fix Architecture FIRST (Before Adding Features)

This MUST be done before implementing new features to avoid compounding technical debt.

#### 0.1 Repository Layer Cleanup

**Goal:** Repositories should ONLY handle data access, not domain logic.

##### Current Problems:
```python
# ❌ BAD: Repository modifying domain model
class EmployeeHierarchyRepository:
    def remove_supervisor(self, target: Employee):
        # ... database operations ...
        target.supervisor = None  # ❌ Domain logic in repository!
    
    def assign_supervisor(self, target: Employee, supervisor: Employee):
        # ... database operations ...
        target.supervisor = supervisor  # ❌ Domain logic in repository!
```

##### Refactored Solution:
```python
# ✅ GOOD: Repository only handles data persistence
class EmployeeHierarchyRepository:
    """Repository for employee hierarchy closure table operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # === Core CRUD Operations ===
    
    def get_all_employees(self) -> list[Employee]:
        """Get all employees from the database."""
        return list(self.session.exec(select(Employee)).all())
    
    def get_employee_by_id(self, user_id: uuid.UUID) -> Optional[Employee]:
        """Get employee by user_id."""
        return self.session.get(Employee, user_id)
    
    def add_self_reference(self, employee: Employee) -> None:
        """Add self-reference entry (depth=0) for an employee."""
        element = EmployeeHierarchy(
            ancestor_id=employee.user_id,
            descendant_id=employee.user_id,
            depth=0
        )
        self.session.add(element)
    
    def delete_hierarchy_paths(
        self,
        ancestor_ids: list[uuid.UUID],
        descendant_ids: list[uuid.UUID]
    ) -> None:
        """Delete specific paths from hierarchy table."""
        exec_del = delete(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id.in_(ancestor_ids),
            EmployeeHierarchy.descendant_id.in_(descendant_ids),
        )
        self.session.exec(exec_del)
    
    def insert_hierarchy_paths(
        self,
        ancestor_ids: list[uuid.UUID],
        descendant_ids: list[uuid.UUID]
    ) -> None:
        """Insert new paths into hierarchy table.
        
        Creates all combinations of ancestors and descendants with correct depths.
        """
        paths = []
        for i, ancestor_id in enumerate(ancestor_ids):
            for j, descendant_id in enumerate(descendant_ids):
                paths.append(
                    EmployeeHierarchy(
                        ancestor_id=ancestor_id,
                        descendant_id=descendant_id,
                        depth=i + j + 1
                    )
                )
        self.session.add_all(paths)
    
    def clear_all_hierarchy(self) -> int:
        """Delete all hierarchy records. Returns count of deleted records."""
        result = self.session.exec(delete(EmployeeHierarchy))
        return result.rowcount  # type: ignore
    
    # === Query Operations ===
    
    def get_ancestor_ids(
        self,
        descendant_id: uuid.UUID,
        include_self: bool = False
    ) -> list[uuid.UUID]:
        """Get all ancestor IDs for a given employee."""
        stmt = (
            select(EmployeeHierarchy.ancestor_id)
            .where(EmployeeHierarchy.descendant_id == descendant_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
            .order_by(EmployeeHierarchy.depth.asc())
        )
        return list(self.session.scalars(stmt).all())
    
    def get_descendant_ids(
        self,
        ancestor_id: uuid.UUID,
        include_self: bool = False
    ) -> list[uuid.UUID]:
        """Get all descendant IDs for a given employee."""
        stmt = (
            select(EmployeeHierarchy.descendant_id)
            .where(EmployeeHierarchy.ancestor_id == ancestor_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
            .order_by(EmployeeHierarchy.depth.asc())
        )
        return list(self.session.scalars(stmt).all())
    
    def get_subordinates(
        self,
        supervisor_id: uuid.UUID,
        include_self: bool = False
    ) -> list[Employee]:
        """Get all subordinate employees."""
        stmt = (
            select(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.descendant_id,
            )
            .where(EmployeeHierarchy.ancestor_id == supervisor_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
        )
        return list(self.session.scalars(stmt).all())
    
    def get_supervisors(
        self,
        subordinate_id: uuid.UUID,
        include_self: bool = False
    ) -> list[Employee]:
        """Get all supervisor employees."""
        stmt = (
            select(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.ancestor_id,
            )
            .where(EmployeeHierarchy.descendant_id == subordinate_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
        )
        return list(self.session.scalars(stmt).all())
    
    def find_orphaned_employees(self) -> list[Employee]:
        """Find employees with supervisor_id pointing to non-existent employee."""
        stmt = (
            select(Employee)
            .outerjoin(
                Employee,
                Employee.supervisor_id == Employee.user_id,
                isouter=True
            )
            .where(Employee.supervisor_id.isnot(None))
            .where(Employee.supervisor_id.not_in(select(Employee.user_id)))
        )
        return list(self.session.scalars(stmt).all())
    
    def get_hierarchy_statistics(self) -> dict[str, any]:
        """Get basic statistics about hierarchy structure."""
        total_employees = self.session.scalar(
            select(func.count()).select_from(Employee)
        ) or 0
        
        total_records = self.session.scalar(
            select(func.count()).select_from(EmployeeHierarchy)
        ) or 0
        
        max_depth = self.session.scalar(
            select(func.max(EmployeeHierarchy.depth))
        ) or 0
        
        avg_depth = self.session.scalar(
            select(func.avg(EmployeeHierarchy.depth))
        ) or 0.0
        
        employees_without_supervisor = self.session.scalar(
            select(func.count()).select_from(Employee).where(
                Employee.supervisor_id.is_(None)
            )
        ) or 0
        
        return {
            "total_employees": total_employees,
            "total_hierarchy_records": total_records,
            "max_depth": max_depth,
            "avg_depth": float(avg_depth),
            "employees_without_supervisor": employees_without_supervisor,
        }
```

**Key Changes:**
- ✅ No domain model modifications in repository
- ✅ Clear, focused methods with single responsibility
- ✅ Separated read and write operations
- ✅ Better naming (get_ancestor_ids vs get_higher_user_ids)
- ✅ Consistent method signatures

---

#### 0.2 Service Layer Restructuring

**Goal:** Service handles business logic and orchestrates repositories. No direct session access.

##### Current Problems:
```python
# ❌ BAD: Service managing transactions directly
class EmployeeService:
    def __init__(self, employee_repo, employee_hierarchy_repo):
        self.employee_repo = employee_repo
        self.user_repo = employee_repo.user_repo  # ❌ Reaching through dependencies
        self.session = self.user_repo.session      # ❌ Direct session access
    
    def create_employee_for_user(self, employee_in):
        # ... logic ...
        self.session.add(user.employee)  # ❌ Service managing persistence
        self.session.commit()            # ❌ Service managing transactions
```

##### Refactored Solution:
```python
# ✅ GOOD: Clean service with clear boundaries
class EmployeeService:
    """Business logic for employee operations."""
    
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        employee_hierarchy_repo: EmployeeHierarchyRepository,
        user_repo: UserRepository,  # ✅ Explicit dependency
    ):
        self.employee_repo = employee_repo
        self.hierarchy_repo = employee_hierarchy_repo
        self.user_repo = user_repo
    
    # === Domain Logic Methods ===
    
    def create_employee_for_user(self, employee_in: EmployeeCreate) -> Employee:
        """Create an employee record for a user.
        
        Note: This method doesn't commit. Caller is responsible for transaction.
        """
        user = self.user_repo.get_user_by_id(employee_in.user_id)
        if not user:
            raise UserNotFoundError(user_id=employee_in.user_id)
        
        if user.employee:
            raise EmployeeAlreadyExistsError()
        
        # Create employee
        employee = Employee(
            user_id=employee_in.user_id,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
        )
        user.employee = employee
        
        # Add to hierarchy (self-reference)
        self.hierarchy_repo.add_self_reference(employee)
        
        return employee
    
    def assign_supervisor_to_employee(
        self,
        target: Employee,
        supervisor: Employee
    ) -> None:
        """Assign a supervisor to an employee.
        
        Validates the assignment and updates both the Employee model
        and the hierarchy closure table.
        
        Note: This method doesn't commit. Caller is responsible for transaction.
        
        Raises:
            DomainError: If assignment would violate business rules
            HierarchyCycleError: If assignment would create a cycle
        """
        # Validation
        self._validate_supervisor_assignment(target, supervisor)
        
        # If target already has a supervisor, remove it first
        if target.supervisor_id:
            self.remove_supervisor_from_employee(target)
        
        # Update domain model
        target.supervisor_id = supervisor.user_id
        target.supervisor = supervisor
        
        # Update closure table
        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(
            supervisor.user_id, include_self=True
        )
        descendant_ids = self.hierarchy_repo.get_descendant_ids(
            target.user_id, include_self=True
        )
        
        self.hierarchy_repo.insert_hierarchy_paths(ancestor_ids, descendant_ids)
    
    def remove_supervisor_from_employee(self, target: Employee) -> None:
        """Remove supervisor from an employee.
        
        Note: This method doesn't commit. Caller is responsible for transaction.
        """
        if not target.supervisor_id:
            return
        
        # Get paths to delete
        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(target.user_id)
        descendant_ids = self.hierarchy_repo.get_descendant_ids(
            target.user_id, include_self=True
        )
        
        # Delete from closure table
        self.hierarchy_repo.delete_hierarchy_paths(ancestor_ids, descendant_ids)
        
        # Update domain model
        target.supervisor_id = None
        target.supervisor = None
    
    # === Validation Methods ===
    
    def _validate_supervisor_assignment(
        self,
        target: Employee,
        supervisor: Employee
    ) -> None:
        """Validate supervisor assignment before execution."""
        # Check if same employee
        if target.user_id == supervisor.user_id:
            raise DomainError("Employee cannot be their own supervisor")
        
        # Check if would create cycle
        if self.would_create_cycle(target, supervisor):
            raise HierarchyCycleError(
                f"Assigning {supervisor.user_id} as supervisor of "
                f"{target.user_id} would create a cycle"
            )
        
        # Check max depth
        supervisor_depth = self._get_depth(supervisor)
        target_subtree_depth = self._get_subtree_depth(target)
        
        if supervisor_depth + target_subtree_depth + 1 > Settings.EMPLOYEE_MAX_HIERARCHY_LEVELS:
            raise HierarchyDepthExceededError(
                f"Assignment would exceed maximum hierarchy depth of "
                f"{Settings.EMPLOYEE_MAX_HIERARCHY_LEVELS}"
            )
    
    def would_create_cycle(self, target: Employee, supervisor: Employee) -> bool:
        """Check if assignment would create a cycle."""
        # If supervisor is a subordinate of target, it's a cycle
        subordinate_ids = self.hierarchy_repo.get_descendant_ids(target.user_id)
        return supervisor.user_id in subordinate_ids
    
    def _get_depth(self, employee: Employee) -> int:
        """Get the depth of an employee in the hierarchy."""
        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(
            employee.user_id, include_self=False
        )
        return len(ancestor_ids)
    
    def _get_subtree_depth(self, employee: Employee) -> int:
        """Get the maximum depth of the subtree rooted at employee."""
        # This would require a more complex query
        # For now, we can use a simpler approach
        descendants = self.hierarchy_repo.get_subordinates(
            employee.user_id, include_self=True
        )
        if not descendants:
            return 0
        
        max_depth = 0
        for desc in descendants:
            depth = self._get_depth(desc) - self._get_depth(employee)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    # === Query Methods ===
    
    def get_employee_by_user_id(self, user_id: uuid.UUID) -> Optional[Employee]:
        """Get employee by user ID."""
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user.employee
    
    def is_supervisor_of(
        self,
        potential_supervisor: Employee,
        potential_subordinate: Employee,
        include_self: bool = False
    ) -> bool:
        """Check if one employee is a supervisor of another."""
        if include_self and potential_supervisor.user_id == potential_subordinate.user_id:
            return True
        
        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(
            potential_subordinate.user_id, include_self=False
        )
        return potential_supervisor.user_id in ancestor_ids
    
    def get_hierarchy_level_difference(
        self,
        employee1: Employee,
        employee2: Employee
    ) -> Optional[int]:
        """Get the hierarchy level difference between two employees.
        
        Returns:
            Positive if employee1 is higher, negative if lower, 0 if same, None if unrelated
        """
        if employee1.user_id == employee2.user_id:
            return 0
        
        # Check if employee1 is supervisor of employee2
        if self.is_supervisor_of(employee1, employee2):
            depth1 = self._get_depth(employee1)
            depth2 = self._get_depth(employee2)
            return depth2 - depth1  # Positive number
        
        # Check if employee2 is supervisor of employee1
        if self.is_supervisor_of(employee2, employee1):
            depth1 = self._get_depth(employee1)
            depth2 = self._get_depth(employee2)
            return depth2 - depth1  # Negative number
        
        # Not related
        return None
```

**Key Changes:**
- ✅ No direct session access
- ✅ Clear separation: service does logic, repo does persistence
- ✅ Explicit dependencies (no reaching through)
- ✅ Validation methods clearly separated
- ✅ Methods don't commit (caller manages transactions)
- ✅ Better error handling with specific exceptions

---

#### 0.3 Transaction Management with Unit of Work Pattern

**Goal:** Centralize transaction management at the API/endpoint level.

##### Implementation:

```python
# app/core/unit_of_work.py
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session

from app.repositories.employee import EmployeeRepository
from app.repositories.employee_hierarchy import EmployeeHierarchyRepository
from app.repositories.user import UserRepository
from app.services.employee import EmployeeService


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing transactions.
    
    Provides a single transaction boundary for all repository operations.
    """
    
    def __init__(self, session: Session):
        self.session = session
        
        # Initialize repositories
        self.user_repo = UserRepository(session)
        self.employee_repo = EmployeeRepository(session)
        self.hierarchy_repo = EmployeeHierarchyRepository(session)
        
        # Initialize services
        self.employee_service = EmployeeService(
            employee_repo=self.employee_repo,
            employee_hierarchy_repo=self.hierarchy_repo,
            user_repo=self.user_repo,
        )
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.session.rollback()
    
    def flush(self) -> None:
        """Flush pending changes without committing."""
        self.session.flush()


@contextmanager
def unit_of_work(session: Session) -> Generator[UnitOfWork, None, None]:
    """
    Context manager for unit of work.
    
    Usage:
        with unit_of_work(session) as uow:
            uow.employee_service.assign_supervisor(...)
            uow.commit()
    """
    uow = UnitOfWork(session)
    try:
        yield uow
    except Exception:
        uow.rollback()
        raise
```

##### API Endpoint Pattern:

```python
# app/api/employees.py

@router.post(
    "/{target_id}/supervisor/{supervisor_id}",
    name="Assign Supervisor",
    operation_id="assignSupervisor",
    status_code=status.HTTP_200_OK,
)
def assign_supervisor(
    current_user: CurrentUserDep,
    target_id: uuid.UUID,
    supervisor_id: uuid.UUID,
    session: DatabaseSession,
):
    """Assign a supervisor to an employee."""
    with unit_of_work(session) as uow:
        # Get employees
        target = uow.employee_service.get_employee_by_user_id(target_id)
        supervisor = uow.employee_service.get_employee_by_user_id(supervisor_id)
        
        if not target or not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Perform operation
        uow.employee_service.assign_supervisor_to_employee(target, supervisor)
        
        # Commit transaction
        uow.commit()
        
        return {"message": "Supervisor assigned successfully"}
```

**Benefits:**
- ✅ Clear transaction boundaries
- ✅ Automatic rollback on errors
- ✅ Easy to test (can mock UnitOfWork)
- ✅ Consistent pattern across all endpoints
- ✅ Services remain transaction-agnostic

---

#### 0.4 Exception Hierarchy

Create clear exception hierarchy for better error handling:

```python
# app/core/exceptions.py (additions)

class HierarchyError(DomainError):
    """Base exception for hierarchy-related errors."""
    pass


class HierarchyCycleError(HierarchyError):
    """Raised when an operation would create a cycle."""
    pass


class HierarchyDepthExceededError(HierarchyError):
    """Raised when operation would exceed max hierarchy depth."""
    pass


class HierarchyCorruptionError(HierarchyError):
    """Raised when hierarchy data is corrupted."""
    pass


class InvalidSupervisorAssignmentError(HierarchyError):
    """Raised when supervisor assignment is invalid."""
    pass
```

---

#### 0.5 Updated Dependency Injection

```python
# app/api/dependencies.py

from app.core.unit_of_work import UnitOfWork

def get_unit_of_work(session: DatabaseSession) -> UnitOfWork:
    """Provides a Unit of Work dependency."""
    return UnitOfWork(session=session)

UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


# Simplified individual dependencies (for read-only operations)
def get_employee_service(uow: UnitOfWorkDep) -> EmployeeService:
    """Get employee service from UoW."""
    return uow.employee_service

EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]
```

---

#### 0.6 Migration Strategy

**Step-by-step refactoring without breaking existing code:**

1. **Week 1: Add new code alongside old**
   - Create new `UnitOfWork` class
   - Create refactored `EmployeeHierarchyRepository` with new methods
   - Keep old methods working

2. **Week 2: Migrate endpoints one by one**
   - Update one endpoint to use UnitOfWork pattern
   - Test thoroughly
   - Repeat for each endpoint

3. **Week 3: Remove old code**
   - Once all endpoints migrated, remove old methods
   - Update tests
   - Clean up dependencies

4. **Week 4: Add new features**
   - Now safe to add rebuild, validation, etc.

---

#### 0.7 Architecture Comparison Diagram

##### BEFORE (Current - Problematic):
```
┌─────────────────────────────────────────────────────────────┐
│                     API Endpoint Layer                      │
│  - Minimal logic                                            │
│  - Just calls service methods                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  ❌ Business logic + Transaction management                 │
│  ❌ self.session.commit()                                   │
│  ❌ self.session.add()                                      │
│  ❌ Reaches through: employee_repo.user_repo.session        │
└────────────┬──────────────────────────┬─────────────────────┘
             │                          │
             ▼                          ▼
┌────────────────────────┐    ┌────────────────────────────┐
│  EmployeeRepository    │    │ EmployeeHierarchyRepository│
│  ❌ Depends on         │    │ ❌ Modifies domain models  │
│     UserRepository     │    │    target.supervisor = X   │
│  - Has user_repo attr  │    │ ❌ Session operations      │
└────────────┬───────────┘    └────────────┬───────────────┘
             │                              │
             ▼                              ▼
        ┌────────────────────────────────────────┐
        │         Database Session               │
        │  ❌ Accessed from multiple layers      │
        │  ❌ No clear transaction boundaries    │
        └────────────────────────────────────────┘

PROBLEMS:
- Session commits in services
- Repositories modify domain models
- Tangled dependencies (repo → repo → session)
- No clear transaction boundaries
- Hard to test
- Easy to introduce bugs
```

##### AFTER (Refactored - Clean):
```
┌─────────────────────────────────────────────────────────────┐
│                     API Endpoint Layer                      │
│  ✅ Transaction boundaries (with UnitOfWork)                │
│  ✅ Calls service methods                                   │
│  ✅ Handles commit/rollback                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Unit of Work                              │
│  ✅ Creates all repositories and services                   │
│  ✅ Manages transaction lifecycle                           │
│  ✅ commit(), rollback(), flush()                           │
└────────┬──────────────────────────────────┬────────────────┘
         │                                  │
         │  Creates                         │  Creates
         ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  ✅ ONLY business logic and validation                      │
│  ✅ NO session access                                       │
│  ✅ NO commits                                              │
│  ✅ Orchestrates repositories                               │
│  ✅ Clean dependencies (user_repo, employee_repo, etc.)     │
└──────┬──────────────────┬───────────────────┬──────────────┘
       │                  │                   │
       ▼                  ▼                   ▼
┌─────────────┐  ┌──────────────────┐  ┌────────────────────┐
│UserRepo     │  │EmployeeRepo      │  │HierarchyRepo       │
│✅ Data only │  │✅ Data only      │  │✅ Data only        │
│✅ CRUD ops  │  │✅ CRUD ops       │  │✅ NO domain logic  │
└──────┬──────┘  └────────┬─────────┘  └──────┬─────────────┘
       │                  │                    │
       └──────────────────┴────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │         Database Session               │
        │  ✅ Single source of truth             │
        │  ✅ Managed by UnitOfWork              │
        │  ✅ Clear transaction boundaries       │
        └────────────────────────────────────────┘

BENEFITS:
- Clear separation of concerns
- Easy to test (mock UoW)
- Transaction boundaries explicit
- No tangled dependencies
- Repositories are simple data access
- Services are pure business logic
```



## Required Functions

### 1. Hierarchy Rebuild System ⚠️ CRITICAL

#### 1.1 Complete Rebuild
**Purpose:** Rebuild the entire `employee_hierarchy` table from scratch based on `supervisor_id` relationships.

**Use Cases:**
- Data corruption recovery
- Migration from legacy systems
- After manual database fixes
- Testing and validation

**Implementation:**

##### Repository Method
```python
# app/repositories/employee_hierarchy.py

def rebuild_hierarchy_full(self) -> dict[str, int]:
    """
    Completely rebuild the employee hierarchy table.
    
    Returns:
        Statistics about the rebuild (records_deleted, records_created, employees_processed)
    """
```

**Algorithm:**
1. Delete all records from `employee_hierarchy` table
2. For each employee:
   - Add self-reference (depth=0)
   - Traverse up the supervisor chain
   - Create all ancestor-descendant pairs with correct depths
3. Return statistics

##### Service Method
```python
# app/services/employee.py

def rebuild_hierarchy(self) -> dict[str, any]:
    """
    Rebuild the entire employee hierarchy.
    
    Returns:
        Detailed report including statistics, validation results, and any issues found
    """
```

**Process:**
1. Log rebuild start
2. Validate all employees before rebuild
3. Call repository rebuild
4. Validate hierarchy after rebuild
5. Return comprehensive report

##### API Endpoint
```python
# app/api/employees.py

@router.post(
    "/hierarchy/rebuild",
    name="Rebuild Employee Hierarchy",
    operation_id="rebuildEmployeeHierarchy",
    status_code=status.HTTP_200_OK,
)
def rebuild_employee_hierarchy(
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    force: bool = False
):
    """
    Rebuild the entire employee hierarchy table.
    
    ⚠️ ADMIN ONLY - This is a maintenance operation.
    
    Args:
        force: If true, skip confirmation and force rebuild
        
    Returns:
        Rebuild report with statistics and validation results
    """
```

**Security:**
- Require admin/super-admin role
- Log who initiated the rebuild
- Consider adding a confirmation parameter
- Rate limit (1 request per 5 minutes)

---

#### 1.2 Partial/Incremental Rebuild
**Purpose:** Rebuild hierarchy for a specific subtree without affecting the entire hierarchy.

##### Repository Method
```python
def rebuild_hierarchy_subtree(self, root_employee: Employee) -> dict[str, int]:
    """
    Rebuild hierarchy for a specific employee and all their subordinates.
    
    Args:
        root_employee: The top employee of the subtree to rebuild
        
    Returns:
        Statistics about the rebuild for this subtree
    """
```

##### Service Method
```python
def rebuild_hierarchy_for_employee(self, user_id: uuid.UUID) -> dict[str, any]:
    """
    Rebuild hierarchy for a specific employee's subtree.
    
    Args:
        user_id: The employee's user ID
        
    Returns:
        Rebuild report for the subtree
    """
```

##### API Endpoint
```python
@router.post(
    "/hierarchy/rebuild/{user_id}",
    name="Rebuild Employee Subtree",
    operation_id="rebuildEmployeeSubtree",
    status_code=status.HTTP_200_OK,
)
def rebuild_employee_subtree(
    current_user: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep,
):
    """
    Rebuild hierarchy for a specific employee and their subordinates.
    
    ⚠️ ADMIN ONLY
    """
```

---

### 2. Validation & Integrity Checks

#### 2.1 Hierarchy Validation
**Purpose:** Detect inconsistencies, cycles, and data corruption.

##### Repository Method
```python
def validate_hierarchy(self) -> dict[str, list]:
    """
    Validate the hierarchy table for inconsistencies.
    
    Returns:
        Dictionary with lists of issues found:
        - missing_self_references: Employees without depth=0 entry
        - orphaned_hierarchy_records: Hierarchy records for non-existent employees
        - inconsistent_depths: Records with incorrect depth calculations
        - missing_paths: Missing intermediate paths
    """
```

##### Service Method
```python
def validate_employee_hierarchy(self) -> dict[str, any]:
    """
    Comprehensive validation of employee hierarchy.
    
    Returns:
        Validation report with:
        - is_valid: bool
        - issues: list of ValidationIssue objects
        - cycles: list of detected cycles
        - orphans: list of orphaned employees
        - max_depth_violations: employees exceeding max hierarchy depth
    """
```

**Checks:**
1. Cycle detection in supervisor relationships
2. Orphaned employees (supervisor_id points to non-existent employee)
3. Max depth violations
4. Closure table integrity
5. Self-reference presence (depth=0)
6. Consistency between Employee.supervisor_id and hierarchy table

##### API Endpoint
```python
@router.get(
    "/hierarchy/validate",
    name="Validate Employee Hierarchy",
    operation_id="validateEmployeeHierarchy",
    status_code=status.HTTP_200_OK,
)
def validate_employee_hierarchy(
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    detailed: bool = False,
):
    """
    Validate the employee hierarchy for issues.
    
    ⚠️ ADMIN ONLY
    
    Args:
        detailed: Include detailed information about each issue
    """
```

---

#### 2.2 Cycle Detection
**Purpose:** Prevent and detect circular supervisor relationships.

##### Service Method
```python
def detect_cycles(self) -> list[list[uuid.UUID]]:
    """
    Detect cycles in the supervisor relationships.
    
    Returns:
        List of cycles, where each cycle is a list of user_ids forming the cycle
    """
```

##### Validation Before Operations
```python
def validate_supervisor_assignment(
    self, 
    target: Employee, 
    supervisor: Employee
) -> tuple[bool, Optional[str]]:
    """
    Validate if a supervisor assignment would create a cycle.
    
    Returns:
        (is_valid, error_message)
    """
```

---

### 3. Diagnostic & Monitoring Tools

#### 3.1 Hierarchy Statistics
**Purpose:** Provide insights into the hierarchy structure.

##### Service Method
```python
def get_hierarchy_statistics(self) -> dict[str, any]:
    """
    Get statistics about the employee hierarchy.
    
    Returns:
        - total_employees: int
        - total_hierarchy_records: int
        - max_depth: int
        - avg_depth: float
        - employees_without_supervisor: int
        - employees_with_subordinates: int
        - top_level_employees: list[Employee] (no supervisor)
        - deepest_employees: list[tuple[Employee, int]] (employee, depth)
        - subordinate_distribution: dict[int, int] (subordinate_count: employee_count)
    """
```

##### API Endpoint
```python
@router.get(
    "/hierarchy/statistics",
    name="Get Hierarchy Statistics",
    operation_id="getHierarchyStatistics",
    status_code=status.HTTP_200_OK,
)
def get_hierarchy_statistics(
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
):
    """
    Get statistics about the employee hierarchy structure.
    
    ⚠️ ADMIN/MANAGER access recommended
    """
```

---

#### 3.2 Hierarchy Path Visualization
**Purpose:** Get the complete path from an employee to the top of the hierarchy.

##### Service Method
```python
def get_hierarchy_path_to_top(self, employee: Employee) -> list[Employee]:
    """
    Get the complete chain of supervisors from employee to top level.
    
    Returns:
        List of employees from the given employee up to the top (no supervisor)
    """

def get_hierarchy_tree(
    self, 
    root_employee: Employee, 
    max_depth: Optional[int] = None
) -> dict[str, any]:
    """
    Get a tree representation of the hierarchy starting from root_employee.
    
    Returns:
        Nested dictionary representing the tree structure
    """
```

##### API Endpoint
```python
@router.get(
    "/hierarchy/{user_id}/path",
    name="Get Employee Hierarchy Path",
    operation_id="getEmployeeHierarchyPath",
    status_code=status.HTTP_200_OK,
)
def get_employee_hierarchy_path(
    current_user: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep,
):
    """
    Get the complete chain of supervisors for an employee.
    """

@router.get(
    "/hierarchy/{user_id}/tree",
    name="Get Employee Hierarchy Tree",
    operation_id="getEmployeeHierarchyTree",
    status_code=status.HTTP_200_OK,
)
def get_employee_hierarchy_tree(
    current_user: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep,
    max_depth: Optional[int] = None,
):
    """
    Get the hierarchy tree with the employee as root.
    """
```

---

### 4. Bulk Operations

#### 4.1 Bulk Supervisor Assignment
**Purpose:** Efficiently reassign multiple employees to a new supervisor.

##### Service Method
```python
def bulk_assign_supervisor(
    self,
    target_user_ids: list[uuid.UUID],
    supervisor_user_id: uuid.UUID,
    remove_existing: bool = True
) -> dict[str, any]:
    """
    Assign multiple employees to a supervisor in one operation.
    
    Args:
        target_user_ids: List of employee user IDs to update
        supervisor_user_id: The new supervisor's user ID
        remove_existing: Remove existing supervisors first
        
    Returns:
        Report with success/failure counts and any errors
    """
```

##### API Endpoint
```python
@router.post(
    "/hierarchy/bulk-assign",
    name="Bulk Assign Supervisor",
    operation_id="bulkAssignSupervisor",
    status_code=status.HTTP_200_OK,
)
def bulk_assign_supervisor(
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    request: BulkSupervisorAssignment,
):
    """
    Assign multiple employees to a supervisor.
    
    ⚠️ ADMIN ONLY
    """
```

---

#### 4.2 Bulk Remove Supervisors
**Purpose:** Remove supervisors from multiple employees.

##### Service Method
```python
def bulk_remove_supervisors(
    self,
    target_user_ids: list[uuid.UUID]
) -> dict[str, any]:
    """
    Remove supervisors from multiple employees.
    
    Returns:
        Report with success/failure counts
    """
```

---

### 5. Orphan Management

#### 5.1 Orphan Detection
**Purpose:** Find employees with invalid supervisor references.

##### Repository Method
```python
def find_orphaned_employees(self) -> list[Employee]:
    """
    Find employees whose supervisor_id points to a non-existent employee.
    
    Returns:
        List of orphaned employees
    """
```

##### Service Method
```python
def get_orphaned_employees(self) -> list[Employee]:
    """
    Get all orphaned employees with additional context.
    
    Returns:
        List of employees with invalid supervisor references
    """
```

##### API Endpoint
```python
@router.get(
    "/hierarchy/orphans",
    name="Get Orphaned Employees",
    operation_id="getOrphanedEmployees",
    status_code=status.HTTP_200_OK,
)
def get_orphaned_employees(
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
):
    """
    Get employees with invalid supervisor references.
    
    ⚠️ ADMIN ONLY
    """
```

---

#### 5.2 Orphan Cleanup
**Purpose:** Automatically fix orphaned employees.

##### Service Method
```python
def cleanup_orphans(
    self,
    reassign_to: Optional[uuid.UUID] = None,
    remove_supervisor: bool = True
) -> dict[str, any]:
    """
    Fix orphaned employees.
    
    Args:
        reassign_to: Optionally reassign all orphans to this supervisor
        remove_supervisor: If True and reassign_to is None, clear supervisor_id
        
    Returns:
        Cleanup report
    """
```

##### API Endpoint
```python
@router.post(
    "/hierarchy/orphans/cleanup",
    name="Cleanup Orphaned Employees",
    operation_id="cleanupOrphanedEmployees",
    status_code=status.HTTP_200_OK,
)
def cleanup_orphaned_employees(
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    request: OrphanCleanupRequest,
):
    """
    Fix orphaned employee references.
    
    ⚠️ ADMIN ONLY
    """
```

---

### 6. Hierarchy Comparison & Diff

#### 6.1 Compare Two Employees
**Purpose:** Get detailed relationship information between employees.

##### Service Method
```python
def compare_employees(
    self,
    employee1: Employee,
    employee2: Employee
) -> dict[str, any]:
    """
    Compare two employees in the hierarchy.
    
    Returns:
        - relationship: str ("same", "supervisor", "subordinate", "unrelated", "peers")
        - level_difference: Optional[int]
        - common_supervisor: Optional[Employee]
        - path_between: Optional[list[Employee]]
    """
```

---

### 7. Integrity Constraints & Safeguards

#### 7.1 Pre-Operation Validation
Add validation before critical operations:

```python
def validate_before_assign(
    self,
    target: Employee,
    supervisor: Employee
) -> None:
    """
    Validate supervisor assignment before executing.
    
    Raises:
        DomainError: If assignment would violate constraints
    """
    # Check for cycles
    # Check max depth
    # Check if supervisor exists
    # Check business rules
```

#### 7.2 Transaction Management
Ensure all hierarchy operations are atomic:

```python
def assign_supervisor_safe(
    self,
    target: Employee,
    supervisor: Employee
) -> None:
    """
    Assign supervisor with full transaction management and rollback on error.
    """
```

---

### 8. Health Check Endpoint

##### API Endpoint
```python
@router.get(
    "/hierarchy/health",
    name="Hierarchy Health Check",
    operation_id="hierarchyHealthCheck",
    status_code=status.HTTP_200_OK,
)
def hierarchy_health_check(
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
):
    """
    Quick health check of the hierarchy system.
    
    Returns:
        - status: "healthy" | "warning" | "critical"
        - issues_found: int
        - last_validation: datetime
        - recommendations: list[str]
    """
```

---

## Schema Additions

### Request Schemas
```python
# app/schemas/employee.py

class BulkSupervisorAssignment(BaseModel):
    target_user_ids: list[uuid.UUID]
    supervisor_user_id: uuid.UUID
    remove_existing: bool = True

class OrphanCleanupRequest(BaseModel):
    reassign_to: Optional[uuid.UUID] = None
    remove_supervisor: bool = True

class HierarchyRebuildRequest(BaseModel):
    force: bool = False
    validate_before: bool = True
    validate_after: bool = True
```

### Response Schemas
```python
class ValidationIssue(BaseModel):
    type: str
    severity: str  # "error", "warning", "info"
    employee_id: Optional[uuid.UUID]
    message: str
    details: Optional[dict]

class HierarchyValidationReport(BaseModel):
    is_valid: bool
    issues: list[ValidationIssue]
    total_issues: int
    errors: int
    warnings: int
    timestamp: datetime

class HierarchyRebuildReport(BaseModel):
    success: bool
    records_deleted: int
    records_created: int
    employees_processed: int
    duration_seconds: float
    validation_report: Optional[HierarchyValidationReport]
    timestamp: datetime

class HierarchyStatistics(BaseModel):
    total_employees: int
    total_hierarchy_records: int
    max_depth: int
    avg_depth: float
    employees_without_supervisor: int
    employees_with_subordinates: int
    top_level_count: int
```

---

## Implementation Priority

### CRITICAL: Architectural Refactoring MUST Come First! ⚠️

**Do NOT implement new features until Phase 0 (Architectural Refactoring) is complete.**

The current implementation has serious architectural flaws that will make new features:
- Harder to implement correctly
- Harder to test
- More likely to introduce bugs
- Impossible to maintain long-term

### Phase 0: Architectural Refactoring (MUST DO FIRST) 🔴
**Estimated: 2-3 weeks**

See "Architectural Refactoring Plan" section for detailed implementation.

**Deliverables:**
1. Clean repository layer (data access only)
2. Clean service layer (business logic only)
3. Unit of Work pattern for transaction management
4. Proper exception hierarchy
5. Updated dependency injection
6. Migrated existing endpoints

**Acceptance Criteria:**
- ✅ No `session.commit()` in services
- ✅ No domain model mutations in repositories
- ✅ All transactions managed at API layer
- ✅ Clear separation of concerns
- ✅ All existing tests passing
- ✅ All endpoints migrated to new pattern

### Phase 1: Critical Features (Implement After Phase 0) 🔴
**Estimated: 2-3 weeks**

1. Complete hierarchy rebuild functionality
2. Basic validation and integrity checks
3. Cycle detection (enhance existing validation)
4. Orphan detection and cleanup

### Phase 2: Important Features 🟡
**Estimated: 2 weeks**

5. Hierarchy statistics and diagnostics
6. Health check endpoint
7. Bulk operations
8. Partial/incremental rebuild

### Phase 3: Nice to Have Features 🟢
**Estimated: 1-2 weeks**

9. Hierarchy path visualization
10. Hierarchy comparison tools
11. Advanced tree operations
12. Historical tracking of hierarchy changes

---

## Testing Requirements

### Unit Tests Required
- Rebuild on empty hierarchy
- Rebuild with simple hierarchy (2-3 levels)
- Rebuild with complex hierarchy (max depth)
- Rebuild with cycles (should detect and handle)
- Rebuild with orphans
- Validation on corrupted data
- Cycle detection accuracy
- Bulk operations atomicity

### Integration Tests Required
- Full rebuild via API endpoint
- Validation and rebuild workflow
- Concurrent modifications during rebuild
- Large hierarchy performance (1000+ employees)

### Performance Tests Required
- Rebuild time for 10k employees
- Validation time for 10k employees
- Query performance after rebuild

---

## Security Considerations

1. **Authentication:** All admin endpoints require admin role
2. **Authorization:** Log all rebuild operations with user info
3. **Rate Limiting:** Prevent DOS via rebuild endpoints
4. **Audit Trail:** Record all structural changes
5. **Confirmation:** Require explicit confirmation for destructive operations
6. **Read-Only Mode:** Consider adding a maintenance mode flag

---

## Monitoring & Alerting

### Metrics to Track
- Hierarchy rebuild frequency
- Validation errors detected
- Orphaned employees count
- Average hierarchy depth
- Max hierarchy depth
- Cycle detection events

### Alerts to Configure
- Critical: Cycles detected
- Warning: Orphans detected
- Warning: Max depth violations
- Info: Hierarchy rebuilt

---

## Configuration

Add to `app/config/settings.py`:

```python
# Hierarchy settings
EMPLOYEE_MAX_HIERARCHY_LEVELS: int = 20
HIERARCHY_REBUILD_COOLDOWN_MINUTES: int = 5
HIERARCHY_VALIDATION_CACHE_MINUTES: int = 15
HIERARCHY_AUTO_VALIDATE_ON_STARTUP: bool = True
```

---

## Database Indexes

Ensure proper indexes exist:

```sql
-- Already exists
CREATE INDEX idx_employee_supervisor ON employees(supervisor_id);

-- Add for hierarchy queries
CREATE INDEX idx_hierarchy_ancestor ON employee_hierarchy(ancestor_id);
CREATE INDEX idx_hierarchy_descendant ON employee_hierarchy(descendant_id);
CREATE INDEX idx_hierarchy_depth ON employee_hierarchy(depth);
CREATE INDEX idx_hierarchy_ancestor_depth ON employee_hierarchy(ancestor_id, depth);
```

---

## Documentation Updates Needed

1. Add rebuild procedures to operations manual
2. Document when to use full vs partial rebuild
3. Create troubleshooting guide for hierarchy issues
4. Add API documentation for all new endpoints
5. Create admin user guide for hierarchy management

---

## Migration Plan

1. Add new methods to repository
2. Add validation and rebuild logic to service
3. Add API endpoints with proper auth
4. Add schemas for requests/responses
5. Write comprehensive tests
6. Update documentation
7. Deploy with monitoring
8. Run initial validation on production data
9. Fix any issues found
10. Schedule regular validation checks

---

## Future Enhancements

1. **Caching:** Cache frequently accessed hierarchy paths
2. **Materialized Views:** For common hierarchy queries
3. **History Tracking:** Track all hierarchy changes over time
4. **Undo/Redo:** Ability to revert hierarchy changes
5. **Import/Export:** Bulk import hierarchy from CSV/JSON
6. **Visualization:** Generate org chart diagrams
7. **Notifications:** Alert supervisors of hierarchy changes
8. **Approval Workflow:** Require approval for sensitive changes

---

## Conclusion

This specification provides a comprehensive production-ready employee hierarchy system with:
- ✅ Robust rebuild capabilities
- ✅ Validation and integrity checks
- ✅ Diagnostic and monitoring tools
- ✅ Bulk operations for efficiency
- ✅ Orphan management
- ✅ Safety mechanisms and safeguards

Implementation should follow the phased approach, prioritizing the rebuild and validation functionality first.
