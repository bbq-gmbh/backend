import uuid

import pytest
from sqlmodel import Session, select

from app.models.employee import Employee
from app.models.employee_hierarchy import EmployeeHierarchy
from app.models.user import User
from app.repositories.employee_hierarchy import EmployeeHierarchyRepository


@pytest.fixture
def hierarchy_repo(session: Session) -> EmployeeHierarchyRepository:
    return EmployeeHierarchyRepository(session)


@pytest.fixture
def sample_users(session: Session) -> list[User]:
    users = [
        User(
            username=f"user{i}",
            password_hash="hashed_password",
            token_key=uuid.uuid4(),
        )
        for i in range(6)
    ]
    for user in users:
        session.add(user)
    session.commit()
    for user in users:
        session.refresh(user)
    return users


@pytest.fixture
def sample_employees(session: Session, sample_users: list[User]) -> list[Employee]:
    from tests.fixtures.user_fixtures import create_test_employee
    
    employees = [
        create_test_employee(session, user.id, f"First{i}", f"Last{i}")
        for i, user in enumerate(sample_users)
    ]
    session.commit()
    for emp in employees:
        session.refresh(emp)
    return employees


class TestAddSelfReference:
    def test_adds_self_reference_with_depth_zero(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        employee = sample_employees[0]
        
        hierarchy_repo.add_self_reference(employee)
        session.commit()
        
        stmt = select(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id == employee.user_id,
            EmployeeHierarchy.descendant_id == employee.user_id,
        )
        result = session.exec(stmt).first()
        
        assert result is not None
        assert result.depth == 0
        assert result.ancestor_id == employee.user_id
        assert result.descendant_id == employee.user_id

    def test_multiple_self_references(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        for employee in sample_employees[:3]:
            hierarchy_repo.add_self_reference(employee)
        session.commit()
        
        stmt = select(EmployeeHierarchy).where(EmployeeHierarchy.depth == 0)
        results = session.exec(stmt).all()
        
        assert len(results) == 3
        for result in results:
            assert result.ancestor_id == result.descendant_id


class TestDeleteHierarchyPaths:
    def test_deletes_specific_paths(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2 = sample_employees[0], sample_employees[1]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.commit()
        
        hierarchy_repo.delete_hierarchy_paths([emp1.user_id], [emp2.user_id])
        session.commit()
        
        stmt = select(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id == emp1.user_id,
            EmployeeHierarchy.descendant_id == emp2.user_id,
        )
        assert session.exec(stmt).first() is None
        
        stmt_self = select(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id == emp1.user_id,
            EmployeeHierarchy.descendant_id == emp1.user_id,
        )
        assert session.exec(stmt_self).first() is not None

    def test_handles_empty_lists(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository
    ):
        hierarchy_repo.delete_hierarchy_paths([], [uuid.uuid4()])
        hierarchy_repo.delete_hierarchy_paths([uuid.uuid4()], [])
        session.commit()

    def test_deletes_multiple_paths(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3 = sample_employees[0], sample_employees[1], sample_employees[2]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp3.user_id, depth=1))
        session.commit()
        
        hierarchy_repo.delete_hierarchy_paths([emp1.user_id], [emp2.user_id, emp3.user_id])
        session.commit()
        
        stmt = select(EmployeeHierarchy).where(EmployeeHierarchy.ancestor_id == emp1.user_id)
        results = session.exec(stmt).all()
        assert len(results) == 0


class TestInsertHierarchyPaths:
    def test_inserts_single_path(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2 = sample_employees[0], sample_employees[1]
        
        hierarchy_repo.insert_hierarchy_paths([emp1.user_id], [emp2.user_id])
        session.commit()
        
        stmt = select(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id == emp1.user_id,
            EmployeeHierarchy.descendant_id == emp2.user_id,
        )
        result = session.exec(stmt).first()
        
        assert result is not None
        assert result.depth == 1

    def test_calculates_correct_depths(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3, emp4 = sample_employees[0:4]
        
        ancestors = [emp1.user_id, emp2.user_id]
        descendants = [emp3.user_id, emp4.user_id]
        
        hierarchy_repo.insert_hierarchy_paths(ancestors, descendants)
        session.commit()
        
        expected_depths = {
            (emp1.user_id, emp3.user_id): 1,
            (emp1.user_id, emp4.user_id): 2,
            (emp2.user_id, emp3.user_id): 2,
            (emp2.user_id, emp4.user_id): 3,
        }
        
        for (anc, desc), expected_depth in expected_depths.items():
            stmt = select(EmployeeHierarchy).where(
                EmployeeHierarchy.ancestor_id == anc,
                EmployeeHierarchy.descendant_id == desc,
            )
            result = session.exec(stmt).first()
            assert result is not None
            assert result.depth == expected_depth

    def test_handles_empty_lists(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository
    ):
        hierarchy_repo.insert_hierarchy_paths([], [uuid.uuid4()])
        hierarchy_repo.insert_hierarchy_paths([uuid.uuid4()], [])
        session.commit()
        
        stmt = select(EmployeeHierarchy)
        assert len(session.exec(stmt).all()) == 0


class TestGetAncestorIds:
    def test_returns_ancestors_without_self(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3 = sample_employees[0], sample_employees[1], sample_employees[2]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp3.user_id, descendant_id=emp3.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp3.user_id, depth=2))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp3.user_id, depth=1))
        session.commit()
        
        ancestors = hierarchy_repo.get_ancestor_ids(emp3.user_id, include_self=False)
        
        assert emp1.user_id in ancestors
        assert emp2.user_id in ancestors
        assert emp3.user_id not in ancestors
        assert len(ancestors) == 2

    def test_returns_ancestors_with_self(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2 = sample_employees[0], sample_employees[1]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.commit()
        
        ancestors = hierarchy_repo.get_ancestor_ids(emp2.user_id, include_self=True)
        
        assert emp1.user_id in ancestors
        assert emp2.user_id in ancestors
        assert len(ancestors) == 2

    def test_ordered_by_depth(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3 = sample_employees[0], sample_employees[1], sample_employees[2]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp3.user_id, descendant_id=emp3.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp3.user_id, depth=2))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp3.user_id, depth=1))
        session.commit()
        
        ancestors = hierarchy_repo.get_ancestor_ids(emp3.user_id, include_self=True)
        
        assert ancestors[0] == emp3.user_id
        assert ancestors[1] == emp2.user_id
        assert ancestors[2] == emp1.user_id


class TestGetDescendantIds:
    def test_returns_descendants_without_self(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3 = sample_employees[0], sample_employees[1], sample_employees[2]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp3.user_id, descendant_id=emp3.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp3.user_id, depth=2))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp3.user_id, depth=1))
        session.commit()
        
        descendants = hierarchy_repo.get_descendant_ids(emp1.user_id, include_self=False)
        
        assert emp2.user_id in descendants
        assert emp3.user_id in descendants
        assert emp1.user_id not in descendants
        assert len(descendants) == 2

    def test_returns_descendants_with_self(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2 = sample_employees[0], sample_employees[1]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.commit()
        
        descendants = hierarchy_repo.get_descendant_ids(emp1.user_id, include_self=True)
        
        assert emp1.user_id in descendants
        assert emp2.user_id in descendants


class TestGetSubordinates:
    def test_returns_subordinate_employees(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3 = sample_employees[0], sample_employees[1], sample_employees[2]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp3.user_id, descendant_id=emp3.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp3.user_id, depth=2))
        session.commit()
        
        subordinates = hierarchy_repo.get_subordinates(emp1.user_id, include_self=False)
        
        subordinate_ids = [s.user_id for s in subordinates]
        assert emp2.user_id in subordinate_ids
        assert emp3.user_id in subordinate_ids
        assert emp1.user_id not in subordinate_ids

    def test_includes_self_when_requested(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2 = sample_employees[0], sample_employees[1]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.commit()
        
        subordinates = hierarchy_repo.get_subordinates(emp1.user_id, include_self=True)
        
        subordinate_ids = [s.user_id for s in subordinates]
        assert emp1.user_id in subordinate_ids
        assert emp2.user_id in subordinate_ids


class TestGetSupervisors:
    def test_returns_supervisor_employees(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3 = sample_employees[0], sample_employees[1], sample_employees[2]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp3.user_id, descendant_id=emp3.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp3.user_id, depth=2))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp3.user_id, depth=1))
        session.commit()
        
        supervisors = hierarchy_repo.get_supervisors(emp3.user_id, include_self=False)
        
        supervisor_ids = [s.user_id for s in supervisors]
        assert emp1.user_id in supervisor_ids
        assert emp2.user_id in supervisor_ids
        assert emp3.user_id not in supervisor_ids


class TestGetAllEmployees:
    def test_returns_all_employees(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        all_employees = hierarchy_repo.get_all_employees()
        
        assert len(all_employees) == len(sample_employees)


class TestGetEmployeeById:
    def test_returns_existing_employee(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        employee = sample_employees[0]
        
        result = hierarchy_repo.get_employee_by_id(employee.user_id)
        
        assert result is not None
        assert result.user_id == employee.user_id

    def test_returns_none_for_nonexistent(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository
    ):
        result = hierarchy_repo.get_employee_by_id(uuid.uuid4())
        
        assert result is None


class TestFindOrphanedEmployees:
    def test_finds_employees_with_invalid_supervisor(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1 = sample_employees[0]
        fake_supervisor_id = uuid.uuid4()
        
        emp1.supervisor_id = fake_supervisor_id
        session.commit()
        
        orphans = hierarchy_repo.find_orphaned_employees()
        
        assert len(orphans) == 1
        assert orphans[0].user_id == emp1.user_id

    def test_returns_empty_when_no_orphans(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        orphans = hierarchy_repo.find_orphaned_employees()
        
        assert len(orphans) == 0


class TestGetHierarchyStatistics:
    def test_returns_correct_statistics(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2, emp3 = sample_employees[0], sample_employees[1], sample_employees[2]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp3.user_id, descendant_id=emp3.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp2.user_id, depth=1))
        session.commit()
        
        stats = hierarchy_repo.get_hierarchy_statistics()
        
        assert stats["total_employees"] == len(sample_employees)
        assert stats["total_hierarchy_records"] == 4
        assert stats["max_depth"] == 1
        assert stats["employees_without_supervisor"] == len(sample_employees)


class TestClearAllHierarchy:
    def test_removes_all_records(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        emp1, emp2 = sample_employees[0], sample_employees[1]
        
        session.add(EmployeeHierarchy(ancestor_id=emp1.user_id, descendant_id=emp1.user_id, depth=0))
        session.add(EmployeeHierarchy(ancestor_id=emp2.user_id, descendant_id=emp2.user_id, depth=0))
        session.commit()
        
        count = hierarchy_repo.clear_all_hierarchy()
        session.commit()
        
        assert count == 2
        stmt = select(EmployeeHierarchy)
        assert len(session.exec(stmt).all()) == 0


class TestComplexHierarchy:
    def test_three_level_hierarchy(
        self, session: Session, hierarchy_repo: EmployeeHierarchyRepository, sample_employees: list[Employee]
    ):
        ceo, manager, employee = sample_employees[0], sample_employees[1], sample_employees[2]
        
        hierarchy_repo.add_self_reference(ceo)
        hierarchy_repo.add_self_reference(manager)
        hierarchy_repo.add_self_reference(employee)
        session.commit()
        
        ancestors_for_manager = hierarchy_repo.get_ancestor_ids(ceo.user_id, include_self=True)
        descendants_for_manager = hierarchy_repo.get_descendant_ids(manager.user_id, include_self=True)
        hierarchy_repo.insert_hierarchy_paths(ancestors_for_manager, descendants_for_manager)
        session.commit()
        
        ancestors_for_employee = hierarchy_repo.get_ancestor_ids(manager.user_id, include_self=True)
        descendants_for_employee = hierarchy_repo.get_descendant_ids(employee.user_id, include_self=True)
        hierarchy_repo.insert_hierarchy_paths(ancestors_for_employee, descendants_for_employee)
        session.commit()
        
        ceo_descendants = hierarchy_repo.get_descendant_ids(ceo.user_id, include_self=False)
        assert len(ceo_descendants) == 2
        assert manager.user_id in ceo_descendants
        assert employee.user_id in ceo_descendants
        
        employee_ancestors = hierarchy_repo.get_ancestor_ids(employee.user_id, include_self=False)
        assert len(employee_ancestors) == 2
        assert manager.user_id in employee_ancestors
        assert ceo.user_id in employee_ancestors
        
        stmt = select(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id == ceo.user_id,
            EmployeeHierarchy.descendant_id == employee.user_id,
        )
        result = session.exec(stmt).first()
        assert result is not None
        assert result.depth == 2
