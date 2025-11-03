import uuid

import pytest
from sqlmodel import Session

from app.config.settings import Settings
from app.core.exceptions import (
    EmployeeAlreadyExistsError,
    HierarchyCycleError,
    HierarchyDepthExceededError,
    InvalidSupervisorAssignmentError,
    UserNotFoundError,
)
from app.models.employee import Employee
from app.models.user import User
from app.repositories.employee import EmployeeRepository
from app.repositories.employee_hierarchy import EmployeeHierarchyRepository
from app.repositories.user import UserRepository
from app.schemas.employee import EmployeeCreate
from app.services.employee import EmployeeService


@pytest.fixture
def user_repo(session: Session) -> UserRepository:
    return UserRepository(session)


@pytest.fixture
def employee_repo(session: Session) -> EmployeeRepository:
    return EmployeeRepository(session)


@pytest.fixture
def hierarchy_repo(session: Session) -> EmployeeHierarchyRepository:
    return EmployeeHierarchyRepository(session)


@pytest.fixture
def employee_service(
    employee_repo: EmployeeRepository,
    hierarchy_repo: EmployeeHierarchyRepository,
    user_repo: UserRepository,
) -> EmployeeService:
    return EmployeeService(employee_repo, hierarchy_repo, user_repo)


@pytest.fixture
def sample_user(session: Session) -> User:
    user = User(
        username="testuser",
        password_hash="hashed_password",
        token_key=uuid.uuid4(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def sample_users(session: Session) -> list[User]:
    users = [
        User(
            username=f"user{i}",
            password_hash="hashed_password",
            token_key=uuid.uuid4(),
        )
        for i in range(25)
    ]
    for user in users:
        session.add(user)
    session.commit()
    for user in users:
        session.refresh(user)
    return users


class TestCreateEmployeeForUser:
    def test_creates_employee_successfully(
        self, session: Session, employee_service: EmployeeService, sample_user: User
    ):
        employee_in = EmployeeCreate(
            user_id=sample_user.id,
            first_name="John",
            last_name="Doe",
        )
        
        employee = employee_service.create_employee_for_user(employee_in)
        
        assert employee.user_id == sample_user.id
        assert employee.first_name == "John"
        assert employee.last_name == "Doe"
        assert employee.supervisor_id is None

    def test_creates_self_reference_in_hierarchy(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_user: User
    ):
        employee_in = EmployeeCreate(
            user_id=sample_user.id,
            first_name="John",
            last_name="Doe",
        )
        
        employee = employee_service.create_employee_for_user(employee_in)
        
        ancestors = hierarchy_repo.get_ancestor_ids(employee.user_id, include_self=True)
        assert len(ancestors) == 1
        assert ancestors[0] == employee.user_id

    def test_raises_error_for_nonexistent_user(
        self, session: Session, employee_service: EmployeeService
    ):
        employee_in = EmployeeCreate(
            user_id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
        )
        
        with pytest.raises(UserNotFoundError):
            employee_service.create_employee_for_user(employee_in)

    def test_raises_error_if_employee_already_exists(
        self, session: Session, employee_service: EmployeeService, sample_user: User
    ):
        employee = Employee(
            user_id=sample_user.id,
            first_name="Existing",
            last_name="Employee",
        )
        sample_user.employee = employee
        session.add(employee)
        session.commit()
        
        employee_in = EmployeeCreate(
            user_id=sample_user.id,
            first_name="New",
            last_name="Employee",
        )
        
        with pytest.raises(EmployeeAlreadyExistsError):
            employee_service.create_employee_for_user(employee_in)


class TestAssignSupervisorToEmployee:
    def test_assigns_supervisor_successfully(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        supervisor_emp = Employee(user_id=sample_users[0].id, first_name="Super", last_name="Visor")
        target_emp = Employee(user_id=sample_users[1].id, first_name="Target", last_name="Employee")
        
        session.add(supervisor_emp)
        session.add(target_emp)
        session.commit()
        
        hierarchy_repo.add_self_reference(supervisor_emp)
        hierarchy_repo.add_self_reference(target_emp)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(target_emp, supervisor_emp)
        
        session.refresh(target_emp)
        assert target_emp.supervisor_id == supervisor_emp.user_id

    def test_creates_hierarchy_paths(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        supervisor_emp = Employee(user_id=sample_users[0].id, first_name="Super", last_name="Visor")
        target_emp = Employee(user_id=sample_users[1].id, first_name="Target", last_name="Employee")
        
        session.add(supervisor_emp)
        session.add(target_emp)
        session.commit()
        
        hierarchy_repo.add_self_reference(supervisor_emp)
        hierarchy_repo.add_self_reference(target_emp)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(target_emp, supervisor_emp)
        
        ancestors = hierarchy_repo.get_ancestor_ids(target_emp.user_id, include_self=False)
        assert supervisor_emp.user_id in ancestors

    def test_replaces_existing_supervisor(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        old_supervisor = Employee(user_id=sample_users[0].id, first_name="Old", last_name="Super")
        new_supervisor = Employee(user_id=sample_users[1].id, first_name="New", last_name="Super")
        target_emp = Employee(user_id=sample_users[2].id, first_name="Target", last_name="Employee")
        
        session.add_all([old_supervisor, new_supervisor, target_emp])
        session.commit()
        
        hierarchy_repo.add_self_reference(old_supervisor)
        hierarchy_repo.add_self_reference(new_supervisor)
        hierarchy_repo.add_self_reference(target_emp)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(target_emp, old_supervisor)
        session.refresh(target_emp)
        assert target_emp.supervisor_id == old_supervisor.user_id
        
        employee_service.assign_supervisor_to_employee(target_emp, new_supervisor)
        session.refresh(target_emp)
        assert target_emp.supervisor_id == new_supervisor.user_id
        
        ancestors = hierarchy_repo.get_ancestor_ids(target_emp.user_id, include_self=False)
        assert new_supervisor.user_id in ancestors
        assert old_supervisor.user_id not in ancestors

    def test_prevents_self_assignment(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        employee = Employee(user_id=sample_users[0].id, first_name="Test", last_name="Employee")
        session.add(employee)
        session.commit()
        
        hierarchy_repo.add_self_reference(employee)
        session.commit()
        
        with pytest.raises(InvalidSupervisorAssignmentError):
            employee_service.assign_supervisor_to_employee(employee, employee)

    def test_prevents_cycle_creation(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        emp1 = Employee(user_id=sample_users[0].id, first_name="Employee", last_name="One")
        emp2 = Employee(user_id=sample_users[1].id, first_name="Employee", last_name="Two")
        
        session.add_all([emp1, emp2])
        session.commit()
        
        hierarchy_repo.add_self_reference(emp1)
        hierarchy_repo.add_self_reference(emp2)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(emp2, emp1)
        
        with pytest.raises(HierarchyCycleError):
            employee_service.assign_supervisor_to_employee(emp1, emp2)

    def test_prevents_depth_exceeded(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        employees = []
        for i in range(Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS + 2):
            emp = Employee(user_id=sample_users[i].id, first_name=f"Emp{i}", last_name="Test")
            session.add(emp)
            employees.append(emp)
        session.commit()
        
        for emp in employees:
            hierarchy_repo.add_self_reference(emp)
        session.commit()
        
        for i in range(1, Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS + 1):
            employee_service.assign_supervisor_to_employee(employees[i], employees[i - 1])
        
        with pytest.raises(HierarchyDepthExceededError):
            employee_service.assign_supervisor_to_employee(
                employees[Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS + 1], 
                employees[Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS]
            )


class TestRemoveSupervisorFromEmployee:
    def test_removes_supervisor_successfully(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        supervisor = Employee(user_id=sample_users[0].id, first_name="Super", last_name="Visor")
        target = Employee(user_id=sample_users[1].id, first_name="Target", last_name="Employee")
        
        session.add_all([supervisor, target])
        session.commit()
        
        hierarchy_repo.add_self_reference(supervisor)
        hierarchy_repo.add_self_reference(target)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(target, supervisor)
        session.refresh(target)
        assert target.supervisor_id == supervisor.user_id
        
        employee_service.remove_supervisor_from_employee(target)
        session.refresh(target)
        assert target.supervisor_id is None

    def test_removes_hierarchy_paths(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        supervisor = Employee(user_id=sample_users[0].id, first_name="Super", last_name="Visor")
        target = Employee(user_id=sample_users[1].id, first_name="Target", last_name="Employee")
        
        session.add_all([supervisor, target])
        session.commit()
        
        hierarchy_repo.add_self_reference(supervisor)
        hierarchy_repo.add_self_reference(target)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(target, supervisor)
        
        ancestors_before = hierarchy_repo.get_ancestor_ids(target.user_id, include_self=False)
        assert len(ancestors_before) == 1
        
        employee_service.remove_supervisor_from_employee(target)
        
        ancestors_after = hierarchy_repo.get_ancestor_ids(target.user_id, include_self=False)
        assert len(ancestors_after) == 0

    def test_handles_no_supervisor_gracefully(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        target = Employee(user_id=sample_users[0].id, first_name="Target", last_name="Employee")
        session.add(target)
        session.commit()
        
        hierarchy_repo.add_self_reference(target)
        session.commit()
        
        employee_service.remove_supervisor_from_employee(target)


class TestWouldCreateCycle:
    def test_detects_direct_cycle(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        emp1 = Employee(user_id=sample_users[0].id, first_name="Emp", last_name="One")
        emp2 = Employee(user_id=sample_users[1].id, first_name="Emp", last_name="Two")
        
        session.add_all([emp1, emp2])
        session.commit()
        
        hierarchy_repo.add_self_reference(emp1)
        hierarchy_repo.add_self_reference(emp2)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(emp2, emp1)
        
        assert employee_service.would_create_cycle(emp1, emp2) is True
        assert employee_service.would_create_cycle(emp2, emp1) is False

    def test_detects_indirect_cycle(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        emp1 = Employee(user_id=sample_users[0].id, first_name="Emp", last_name="One")
        emp2 = Employee(user_id=sample_users[1].id, first_name="Emp", last_name="Two")
        emp3 = Employee(user_id=sample_users[2].id, first_name="Emp", last_name="Three")
        
        session.add_all([emp1, emp2, emp3])
        session.commit()
        
        for emp in [emp1, emp2, emp3]:
            hierarchy_repo.add_self_reference(emp)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(emp2, emp1)
        employee_service.assign_supervisor_to_employee(emp3, emp2)
        
        assert employee_service.would_create_cycle(emp1, emp3) is True


class TestIsSupervisorOf:
    def test_direct_supervision(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        supervisor = Employee(user_id=sample_users[0].id, first_name="Super", last_name="Visor")
        subordinate = Employee(user_id=sample_users[1].id, first_name="Sub", last_name="Ordinate")
        
        session.add_all([supervisor, subordinate])
        session.commit()
        
        hierarchy_repo.add_self_reference(supervisor)
        hierarchy_repo.add_self_reference(subordinate)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(subordinate, supervisor)
        
        assert employee_service.is_supervisor_of(supervisor, subordinate) is True
        assert employee_service.is_supervisor_of(subordinate, supervisor) is False

    def test_indirect_supervision(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        ceo = Employee(user_id=sample_users[0].id, first_name="CEO", last_name="Boss")
        manager = Employee(user_id=sample_users[1].id, first_name="Manager", last_name="Middle")
        employee = Employee(user_id=sample_users[2].id, first_name="Employee", last_name="Low")
        
        session.add_all([ceo, manager, employee])
        session.commit()
        
        for emp in [ceo, manager, employee]:
            hierarchy_repo.add_self_reference(emp)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(manager, ceo)
        employee_service.assign_supervisor_to_employee(employee, manager)
        
        assert employee_service.is_supervisor_of(ceo, employee) is True
        assert employee_service.is_supervisor_of(manager, employee) is True

    def test_include_self(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        employee = Employee(user_id=sample_users[0].id, first_name="Emp", last_name="One")
        session.add(employee)
        session.commit()
        
        hierarchy_repo.add_self_reference(employee)
        session.commit()
        
        assert employee_service.is_supervisor_of(employee, employee, include_self=True) is True
        assert employee_service.is_supervisor_of(employee, employee, include_self=False) is False


class TestGetHierarchyLevelDifference:
    def test_same_employee_returns_zero(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        employee = Employee(user_id=sample_users[0].id, first_name="Emp", last_name="One")
        session.add(employee)
        session.commit()
        
        hierarchy_repo.add_self_reference(employee)
        session.commit()
        
        diff = employee_service.get_hierarchy_level_difference(employee, employee)
        assert diff == 0

    def test_direct_supervision_difference(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        supervisor = Employee(user_id=sample_users[0].id, first_name="Super", last_name="Visor")
        subordinate = Employee(user_id=sample_users[1].id, first_name="Sub", last_name="Ordinate")
        
        session.add_all([supervisor, subordinate])
        session.commit()
        
        hierarchy_repo.add_self_reference(supervisor)
        hierarchy_repo.add_self_reference(subordinate)
        session.commit()
        
        employee_service.assign_supervisor_to_employee(subordinate, supervisor)
        
        diff = employee_service.get_hierarchy_level_difference(supervisor, subordinate)
        assert diff == 1

    def test_unrelated_employees_returns_none(
        self, session: Session, employee_service: EmployeeService, hierarchy_repo: EmployeeHierarchyRepository, sample_users: list[User]
    ):
        emp1 = Employee(user_id=sample_users[0].id, first_name="Emp", last_name="One")
        emp2 = Employee(user_id=sample_users[1].id, first_name="Emp", last_name="Two")
        
        session.add_all([emp1, emp2])
        session.commit()
        
        hierarchy_repo.add_self_reference(emp1)
        hierarchy_repo.add_self_reference(emp2)
        session.commit()
        
        diff = employee_service.get_hierarchy_level_difference(emp1, emp2)
        assert diff is None


class TestGetEmployeeByUserId:
    def test_returns_existing_employee(
        self, session: Session, employee_service: EmployeeService, sample_users: list[User]
    ):
        employee = Employee(user_id=sample_users[0].id, first_name="Test", last_name="Employee")
        sample_users[0].employee = employee
        session.add(employee)
        session.commit()
        
        result = employee_service.get_employee_by_user_id(sample_users[0].id)
        
        assert result is not None
        assert result.user_id == sample_users[0].id

    def test_returns_none_for_user_without_employee(
        self, session: Session, employee_service: EmployeeService, sample_users: list[User]
    ):
        result = employee_service.get_employee_by_user_id(sample_users[0].id)
        
        assert result is None

    def test_raises_error_for_nonexistent_user(
        self, session: Session, employee_service: EmployeeService
    ):
        with pytest.raises(UserNotFoundError):
            employee_service.get_employee_by_user_id(uuid.uuid4())
