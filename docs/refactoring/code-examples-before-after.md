# Employee Hierarchy: Before & After Code Examples

This document provides concrete examples of how to refactor the existing code.

---

## Example 1: Repository Layer - Remove Domain Logic

### ❌ BEFORE (Current - Bad)

```python
# app/repositories/employee_hierarchy.py

def remove_supervisor(self, target: Employee):
    ids_upper = self.get_higher_user_ids(target)
    ids_lower = self.get_lower_user_ids(target, same=True)
    
    exec_del = delete(EmployeeHierarchy).where(
        EmployeeHierarchy.ancestor_id.in_(ids_upper),
        EmployeeHierarchy.descendant_id.in_(ids_lower),
    )
    self.session.exec(exec_del)
    
    target.supervisor = None  # ❌ Repository modifying domain model!


def assign_supervisor(self, target: Employee, supervisor: Employee):
    # ... database operations ...
    
    self.session.add_all(all)
    
    target.supervisor = supervisor  # ❌ Repository modifying domain model!
```

**Problems:**
- Repository is modifying the domain model
- Violates single responsibility principle
- Hard to test independently

### ✅ AFTER (Refactored - Good)

```python
# app/repositories/employee_hierarchy.py

def delete_hierarchy_paths(
    self,
    ancestor_ids: list[uuid.UUID],
    descendant_ids: list[uuid.UUID]
) -> None:
    """Delete specific paths from hierarchy table. Data access only."""
    exec_del = delete(EmployeeHierarchy).where(
        EmployeeHierarchy.ancestor_id.in_(ancestor_ids),
        EmployeeHierarchy.descendant_id.in_(descendant_ids),
    )
    self.session.exec(exec_del)
    # ✅ No domain model modification!


def insert_hierarchy_paths(
    self,
    ancestor_ids: list[uuid.UUID],
    descendant_ids: list[uuid.UUID]
) -> None:
    """Insert new paths into hierarchy table. Data access only."""
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
    # ✅ No domain model modification!
```

**Benefits:**
- Repository only handles data persistence
- Clear, focused responsibility
- Easy to test with mocks

---

## Example 2: Service Layer - Remove Transaction Management

### ❌ BEFORE (Current - Bad)

```python
# app/services/employee.py

class EmployeeService:
    def __init__(self, employee_repo, employee_hierarchy_repo):
        self.employee_repo = employee_repo
        self.user_repo = employee_repo.user_repo  # ❌ Reaching through
        self.employee_hierarchy_repo = employee_hierarchy_repo
        self.session = self.user_repo.session  # ❌ Direct session access
    
    def create_employee_for_user(self, employee_in: EmployeeCreate) -> Employee:
        user = self.user_repo.get_user_by_id(employee_in.user_id)
        if not user:
            raise UserNotFoundError(user_id=employee_in.user_id)
        
        if user.employee:
            raise EmployeeAlreadyExistsError()
        
        user.employee = self.employee_repo.create_employee(employee_in)
        self.session.add(user.employee)  # ❌ Service managing persistence
        self.session.add(user)
        
        self.session.commit()  # ❌ Service managing transactions
        self.session.refresh(user.employee)
        return user.employee
    
    def assign_supervisor(self, target: Employee, supervisor: Employee) -> None:
        if target.supervisor:
            raise DomainError("Cannot assign supervisor because it was not None")
        
        target.supervisor = supervisor
        self.employee_hierarchy_repo.assign_supervisor(target, supervisor)
        # ❌ No commit here - inconsistent!
```

**Problems:**
- Service has direct session access
- Commits scattered (sometimes yes, sometimes no)
- Reaching through dependencies
- Hard to control transactions

### ✅ AFTER (Refactored - Good)

```python
# app/services/employee.py

class EmployeeService:
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        employee_hierarchy_repo: EmployeeHierarchyRepository,
        user_repo: UserRepository,  # ✅ Explicit dependency
    ):
        self.employee_repo = employee_repo
        self.hierarchy_repo = employee_hierarchy_repo
        self.user_repo = user_repo
        # ✅ No session access!
    
    def create_employee_for_user(self, employee_in: EmployeeCreate) -> Employee:
        """Create employee. Caller manages transaction."""
        user = self.user_repo.get_user_by_id(employee_in.user_id)
        if not user:
            raise UserNotFoundError(user_id=employee_in.user_id)
        
        if user.employee:
            raise EmployeeAlreadyExistsError()
        
        employee = Employee(
            user_id=employee_in.user_id,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
        )
        user.employee = employee
        
        # Add to hierarchy
        self.hierarchy_repo.add_self_reference(employee)
        
        # ✅ No commit - caller manages transaction
        return employee
    
    def assign_supervisor_to_employee(
        self,
        target: Employee,
        supervisor: Employee
    ) -> None:
        """Assign supervisor. Caller manages transaction."""
        # Validation
        self._validate_supervisor_assignment(target, supervisor)
        
        # Remove existing if present
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
        # ✅ No commit - caller manages transaction
    
    def _validate_supervisor_assignment(
        self,
        target: Employee,
        supervisor: Employee
    ) -> None:
        """Validate assignment. Raises exception if invalid."""
        if target.user_id == supervisor.user_id:
            raise InvalidSupervisorAssignmentError(
                "Employee cannot be their own supervisor"
            )
        
        if self.would_create_cycle(target, supervisor):
            raise HierarchyCycleError(
                f"Assignment would create a cycle"
            )
        
        # Check depth limits
        supervisor_depth = self._get_depth(supervisor)
        target_depth = self._get_subtree_depth(target)
        
        if supervisor_depth + target_depth + 1 > Settings.EMPLOYEE_MAX_HIERARCHY_LEVELS:
            raise HierarchyDepthExceededError(
                f"Would exceed max depth of {Settings.EMPLOYEE_MAX_HIERARCHY_LEVELS}"
            )
```

**Benefits:**
- No transaction management in service
- Clear validation logic
- Easy to test
- Explicit dependencies

---

## Example 3: API Endpoint - Transaction Management with UnitOfWork

### ❌ BEFORE (Current - Bad)

```python
# app/api/employees.py

@router.post("/")
def create_employee(
    _: CurrentUserDep,
    employee_in: EmployeeCreate,
    employee_service: EmployeeServiceDep,
):
    """Create a new employee."""
    # Service handles commit internally
    employee_service.create_employee_for_user(employee_in=employee_in)
    # ❌ No control over transaction
    # ❌ Can't rollback on certain conditions
    # ❌ Can't add additional operations to transaction
```

**Problems:**
- No transaction control at endpoint
- Service commits internally
- Hard to add related operations
- No error recovery

### ✅ AFTER (Refactored - Good)

```python
# app/api/employees.py

@router.post(
    "/",
    name="Create Employee",
    operation_id="createEmployee",
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    current_user: CurrentUserDep,
    employee_in: EmployeeCreate,
    session: DatabaseSession,
):
    """Create a new employee."""
    # ✅ Transaction boundary at endpoint level
    with unit_of_work(session) as uow:
        try:
            # Perform operations
            employee = uow.employee_service.create_employee_for_user(employee_in)
            
            # Could add more operations here in same transaction
            # e.g., create audit log, send notification, etc.
            
            # ✅ Explicit commit
            uow.commit()
            
            return employee
            
        except (UserNotFoundError, EmployeeAlreadyExistsError) as e:
            # ✅ Automatic rollback via context manager
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


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
        try:
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
            
            # ✅ Explicit commit
            uow.commit()
            
            return {
                "message": "Supervisor assigned successfully",
                "target_id": str(target_id),
                "supervisor_id": str(supervisor_id)
            }
            
        except HierarchyCycleError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Would create cycle: {str(e)}"
            )
        except HierarchyDepthExceededError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Depth limit exceeded: {str(e)}"
            )
        except DomainError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
```

**Benefits:**
- ✅ Clear transaction boundaries
- ✅ Easy to add operations to transaction
- ✅ Automatic rollback on errors
- ✅ Better error handling
- ✅ Easy to test

---

## Example 4: Dependencies - Clean Dependency Injection

### ❌ BEFORE (Current - Bad)

```python
# app/api/dependencies.py

def get_employee_repository(user_repo: UserRepositoryDep) -> EmployeeRepository:
    """Provides an employee repository dependency."""
    return EmployeeRepository(user_repo=user_repo)  # ❌ Tangled dependencies


def get_employee_service(
    employee_repo: EmployeeRepositoryDep,
    employee_hierarchy_repo: EmployeeHierarchyRepositoryDep,
) -> EmployeeService:
    """Provides an employee service dependency."""
    return EmployeeService(
        employee_repo=employee_repo,
        employee_hierarchy_repo=employee_hierarchy_repo
    )  # ❌ Service will reach through to get session
```

**Problems:**
- EmployeeRepository needs UserRepository
- Service reaches through dependencies
- Session passed implicitly

### ✅ AFTER (Refactored - Good)

```python
# app/api/dependencies.py

from app.core.unit_of_work import UnitOfWork

def get_unit_of_work(session: DatabaseSession) -> UnitOfWork:
    """Provides a Unit of Work dependency."""
    return UnitOfWork(session=session)  # ✅ Clean, single entry point

UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


# For read-only operations that don't need transaction control
def get_employee_service_readonly(session: DatabaseSession) -> EmployeeService:
    """Get employee service for read-only operations."""
    user_repo = UserRepository(session)
    employee_repo = EmployeeRepository(session)
    hierarchy_repo = EmployeeHierarchyRepository(session)
    
    return EmployeeService(
        employee_repo=employee_repo,
        employee_hierarchy_repo=hierarchy_repo,
        user_repo=user_repo,  # ✅ Explicit dependency
    )

EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service_readonly)]
```

**Benefits:**
- ✅ Clear dependency graph
- ✅ Single source for all services/repos
- ✅ Easy to mock for testing
- ✅ Consistent pattern

---

## Example 5: Testing - Before & After

### ❌ BEFORE (Current - Hard to Test)

```python
# tests/unit/test_employee_service.py

def test_assign_supervisor():
    # ❌ Need real database because service commits
    # ❌ Hard to test transaction boundaries
    # ❌ Have to mock session.commit()
    
    session = TestingSessionLocal()
    user_repo = UserRepository(session)
    employee_repo = EmployeeRepository(user_repo)
    hierarchy_repo = EmployeeHierarchyRepository(session)
    service = EmployeeService(employee_repo, hierarchy_repo)
    
    # Create test data in DB
    # ...
    
    # ❌ Service commits internally, hard to verify behavior
    service.assign_supervisor(target, supervisor)
```

### ✅ AFTER (Refactored - Easy to Test)

```python
# tests/unit/test_employee_service.py

from unittest.mock import Mock, MagicMock
import pytest

def test_assign_supervisor_to_employee():
    # ✅ Pure unit test with mocks
    # ✅ No database needed
    # ✅ Test business logic in isolation
    
    # Arrange
    mock_employee_repo = Mock(spec=EmployeeRepository)
    mock_hierarchy_repo = Mock(spec=EmployeeHierarchyRepository)
    mock_user_repo = Mock(spec=UserRepository)
    
    service = EmployeeService(
        employee_repo=mock_employee_repo,
        employee_hierarchy_repo=mock_hierarchy_repo,
        user_repo=mock_user_repo,
    )
    
    target = Employee(user_id=uuid.uuid4(), first_name="John", last_name="Doe")
    supervisor = Employee(user_id=uuid.uuid4(), first_name="Jane", last_name="Smith")
    
    # Mock repository responses
    mock_hierarchy_repo.get_ancestor_ids.return_value = [supervisor.user_id]
    mock_hierarchy_repo.get_descendant_ids.return_value = [target.user_id]
    
    # Act
    service.assign_supervisor_to_employee(target, supervisor)
    
    # Assert
    assert target.supervisor_id == supervisor.user_id
    mock_hierarchy_repo.insert_hierarchy_paths.assert_called_once()


def test_assign_supervisor_prevents_cycle():
    # ✅ Easy to test validation logic
    
    # Arrange
    mock_hierarchy_repo = Mock(spec=EmployeeHierarchyRepository)
    mock_hierarchy_repo.get_descendant_ids.return_value = [
        uuid.uuid4(),  # supervisor is in target's descendant tree
    ]
    
    service = EmployeeService(
        employee_repo=Mock(),
        employee_hierarchy_repo=mock_hierarchy_repo,
        user_repo=Mock(),
    )
    
    target = Employee(user_id=uuid.uuid4(), first_name="John", last_name="Doe")
    supervisor = Employee(
        user_id=mock_hierarchy_repo.get_descendant_ids.return_value[0],
        first_name="Jane",
        last_name="Smith"
    )
    
    # Act & Assert
    with pytest.raises(HierarchyCycleError):
        service.assign_supervisor_to_employee(target, supervisor)
```

**Benefits:**
- ✅ Fast unit tests (no database)
- ✅ Test business logic in isolation
- ✅ Easy to test edge cases
- ✅ Clear test intentions

---

## Summary: Key Refactoring Principles

### 1. **Repositories: Data Access Only**
```python
# ❌ BAD
def some_repo_method(self, entity):
    # database operations
    entity.field = value  # ❌ Don't modify domain models

# ✅ GOOD
def some_repo_method(self, entity_id):
    # Only database operations
    return data  # ✅ Return data, don't modify
```

### 2. **Services: Business Logic Only**
```python
# ❌ BAD
def some_service_method(self, data):
    # business logic
    self.session.commit()  # ❌ Don't manage transactions

# ✅ GOOD
def some_service_method(self, data):
    # business logic
    # validation
    # orchestrate repositories
    # ✅ Return result, don't commit
```

### 3. **Endpoints: Transaction Boundaries**
```python
# ❌ BAD
def some_endpoint(service: ServiceDep):
    service.do_something()  # ❌ No transaction control

# ✅ GOOD
def some_endpoint(session: DatabaseSession):
    with unit_of_work(session) as uow:
        uow.service.do_something()
        uow.commit()  # ✅ Explicit transaction control
```

### 4. **Dependencies: Clear & Explicit**
```python
# ❌ BAD
class Service:
    def __init__(self, repo):
        self.other_repo = repo.other_repo  # ❌ Reaching through
        self.session = repo.session  # ❌ Implicit access

# ✅ GOOD
class Service:
    def __init__(self, repo, other_repo, session):
        self.repo = repo  # ✅ Explicit
        self.other_repo = other_repo  # ✅ Explicit
        # ✅ Or better: no session at all!
```

---

## Quick Reference: What Goes Where?

| Layer | Responsibilities | Should NOT Do |
|-------|-----------------|---------------|
| **Repository** | - Database queries<br>- CRUD operations<br>- Data mapping | - Modify domain models<br>- Business logic<br>- Validation<br>- Commits |
| **Service** | - Business logic<br>- Validation<br>- Orchestration<br>- Domain rules | - Direct database access<br>- Transaction management<br>- HTTP concerns |
| **API/Endpoint** | - HTTP handling<br>- Transaction boundaries<br>- Auth/permissions<br>- Request/response mapping | - Business logic<br>- Database queries<br>- Validation rules |
| **Unit of Work** | - Transaction lifecycle<br>- Create services/repos<br>- Commit/rollback | - Business logic<br>- Data access |

---

This document should be used alongside the main specification and checklist for a complete refactoring guide.
