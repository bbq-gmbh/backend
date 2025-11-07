"""Integration tests for employee deletion with hierarchy healing."""

from tests.fixtures.user_fixtures import create_test_employee


class TestDeleteEmployee:
    """Test DELETE /employees/{user_id} endpoint."""

    def test_delete_employee_requires_auth(self, client, session):
        """Test that deleting employee requires authentication."""
        from app.models.user import User
        from app.core.security import hash_password

        user = User(username="todelete", password_hash=hash_password("password123"))
        session.add(user)
        session.commit()
        session.refresh(user)

        create_test_employee(session, user.id, "To", "Delete")
        session.commit()

        response = client.delete(f"/employees/{user.id}")
        assert response.status_code == 403

    def test_delete_employee_requires_superuser(self, client, authenticated_client, session):
        """Test that deleting employee requires superuser."""
        from app.models.user import User
        from app.core.security import hash_password

        user = User(username="todelete2", password_hash=hash_password("password123"))
        session.add(user)
        session.commit()
        session.refresh(user)

        create_test_employee(session, user.id, "To", "Delete")
        session.commit()

        response = authenticated_client.delete(f"/employees/{user.id}")
        assert response.status_code == 403

    def test_delete_employee_heals_simple_hierarchy(self, client, superuser_client, session):
        """Test deleting middle employee heals hierarchy: A -> B -> C becomes A -> C."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create A -> B -> C hierarchy
        user_a = User(username="emp_a", password_hash=hash_password("password123"))
        user_b = User(username="emp_b", password_hash=hash_password("password123"))
        user_c = User(username="emp_c", password_hash=hash_password("password123"))
        session.add_all([user_a, user_b, user_c])
        session.commit()

        emp_a = create_test_employee(session, user_a.id, "Employee", "A")
        emp_b = create_test_employee(session, user_b.id, "Employee", "B", supervisor_id=user_a.id)
        emp_c = create_test_employee(session, user_c.id, "Employee", "C", supervisor_id=user_b.id)
        session.commit()

        # Set up hierarchy
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository

        employee_service = EmployeeService(
            EmployeeRepository(session),
            hierarchy_repo,
            UserRepository(session)
        )
        hierarchy_repo.add_self_reference(emp_a)
        hierarchy_repo.add_self_reference(emp_b)
        hierarchy_repo.add_self_reference(emp_c)
        employee_service.assign_supervisor_to_employee(emp_b, emp_a)
        employee_service.assign_supervisor_to_employee(emp_c, emp_b)

        # Verify initial hierarchy: C should have both A and B as ancestors
        ancestors_before = hierarchy_repo.get_ancestor_ids(user_c.id, include_self=False)
        assert user_b.id in ancestors_before
        assert user_a.id in ancestors_before

        # Delete B
        response = superuser_client.delete(f"/employees/{user_b.id}")
        assert response.status_code == 204

        # Verify B is deleted
        session.expire_all()
        deleted_emp = session.get(Employee, user_b.id)
        assert deleted_emp is None

        # Verify user B still exists
        user_b_check = session.get(User, user_b.id)
        assert user_b_check is not None
        assert user_b_check.employee is None

        # Verify C now reports to A
        emp_c_updated = session.get(Employee, user_c.id)
        assert emp_c_updated is not None
        assert emp_c_updated.supervisor_id == user_a.id

        # Verify hierarchy: C should only have A as ancestor
        ancestors_after = hierarchy_repo.get_ancestor_ids(user_c.id, include_self=False)
        assert user_a.id in ancestors_after
        assert user_b.id not in ancestors_after

    def test_delete_employee_with_multiple_subordinates(self, client, superuser_client, session):
        """Test deleting employee with multiple subordinates heals all of them."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create A -> B -> (C, D, E) hierarchy
        user_a = User(username="emp_a2", password_hash=hash_password("password123"))
        user_b = User(username="emp_b2", password_hash=hash_password("password123"))
        user_c = User(username="emp_c2", password_hash=hash_password("password123"))
        user_d = User(username="emp_d2", password_hash=hash_password("password123"))
        user_e = User(username="emp_e2", password_hash=hash_password("password123"))
        session.add_all([user_a, user_b, user_c, user_d, user_e])
        session.commit()

        emp_a = create_test_employee(session, user_a.id, "Emp", "A")
        emp_b = create_test_employee(session, user_b.id, "Emp", "B", supervisor_id=user_a.id)
        emp_c = create_test_employee(session, user_c.id, "Emp", "C", supervisor_id=user_b.id)
        emp_d = create_test_employee(session, user_d.id, "Emp", "D", supervisor_id=user_b.id)
        emp_e = create_test_employee(session, user_e.id, "Emp", "E", supervisor_id=user_b.id)
        session.add_all([emp_a, emp_b, emp_c, emp_d, emp_e])
        session.commit()

        # Set up hierarchy
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository

        employee_service = EmployeeService(
            EmployeeRepository(session),
            hierarchy_repo,
            UserRepository(session)
        )
        
        for emp in [emp_a, emp_b, emp_c, emp_d, emp_e]:
            hierarchy_repo.add_self_reference(emp)
        
        employee_service.assign_supervisor_to_employee(emp_b, emp_a)
        employee_service.assign_supervisor_to_employee(emp_c, emp_b)
        employee_service.assign_supervisor_to_employee(emp_d, emp_b)
        employee_service.assign_supervisor_to_employee(emp_e, emp_b)

        # Delete B
        response = superuser_client.delete(f"/employees/{user_b.id}")
        assert response.status_code == 204

        # Verify all subordinates now report to A
        session.expire_all()
        for user in [user_c, user_d, user_e]:
            emp = session.get(Employee, user.id)
            assert emp is not None
            assert emp.supervisor_id == user_a.id

        # Verify hierarchy
        for user in [user_c, user_d, user_e]:
            ancestors = hierarchy_repo.get_ancestor_ids(user.id, include_self=False)
            assert user_a.id in ancestors
            assert user_b.id not in ancestors

    def test_delete_top_level_employee_with_subordinates(self, client, superuser_client, session):
        """Test deleting top-level employee makes subordinates top-level."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create A -> (B, C) hierarchy (A has no supervisor)
        user_a = User(username="emp_a3", password_hash=hash_password("password123"))
        user_b = User(username="emp_b3", password_hash=hash_password("password123"))
        user_c = User(username="emp_c3", password_hash=hash_password("password123"))
        session.add_all([user_a, user_b, user_c])
        session.commit()

        emp_a = create_test_employee(session, user_a.id, "Top", "Level")
        emp_b = create_test_employee(session, user_b.id, "Sub", "B", supervisor_id=user_a.id)
        emp_c = create_test_employee(session, user_c.id, "Sub", "C", supervisor_id=user_a.id)
        session.add_all([emp_a, emp_b, emp_c])
        session.commit()

        # Set up hierarchy
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository

        employee_service = EmployeeService(
            EmployeeRepository(session),
            hierarchy_repo,
            UserRepository(session)
        )
        
        for emp in [emp_a, emp_b, emp_c]:
            hierarchy_repo.add_self_reference(emp)
        
        employee_service.assign_supervisor_to_employee(emp_b, emp_a)
        employee_service.assign_supervisor_to_employee(emp_c, emp_a)

        # Delete A
        response = superuser_client.delete(f"/employees/{user_a.id}")
        assert response.status_code == 204

        # Verify B and C are now top-level (no supervisor)
        session.expire_all()
        for user in [user_b, user_c]:
            emp = session.get(Employee, user.id)
            assert emp is not None
            assert emp.supervisor_id is None

        # Verify hierarchy: only self-references remain
        for user in [user_b, user_c]:
            ancestors = hierarchy_repo.get_ancestor_ids(user.id, include_self=False)
            assert len(ancestors) == 0

    def test_delete_employee_without_subordinates(self, client, superuser_client, session):
        """Test deleting leaf employee works correctly."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create A -> B (B is a leaf)
        user_a = User(username="emp_a4", password_hash=hash_password("password123"))
        user_b = User(username="emp_b4", password_hash=hash_password("password123"))
        session.add_all([user_a, user_b])
        session.commit()

        emp_a = create_test_employee(session, user_a.id, "Boss", "A")
        emp_b = create_test_employee(session, user_b.id, "Leaf", "B", supervisor_id=user_a.id)
        session.add_all([emp_a, emp_b])
        session.commit()

        # Set up hierarchy
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository

        employee_service = EmployeeService(
            EmployeeRepository(session),
            hierarchy_repo,
            UserRepository(session)
        )
        
        hierarchy_repo.add_self_reference(emp_a)
        hierarchy_repo.add_self_reference(emp_b)
        employee_service.assign_supervisor_to_employee(emp_b, emp_a)

        # Delete B
        response = superuser_client.delete(f"/employees/{user_b.id}")
        assert response.status_code == 204

        # Verify B is deleted
        session.expire_all()
        deleted_emp = session.get(Employee, user_b.id)
        assert deleted_emp is None

        # Verify A is unaffected
        emp_a_check = session.get(Employee, user_a.id)
        assert emp_a_check is not None

    def test_delete_employee_not_found(self, client, superuser_client, session):
        """Test deleting non-existent employee returns 404."""
        import uuid
        
        fake_id = uuid.uuid4()
        response = superuser_client.delete(f"/employees/{fake_id}")
        assert response.status_code == 404


class TestDeleteUserWithEmployee:
    """Test that deleting a user with an employee also heals the hierarchy."""

    def test_delete_user_heals_hierarchy(self, client, superuser_client, session):
        """Test that DELETE /users/{id} also heals the hierarchy."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create A -> B -> C hierarchy
        user_a = User(username="user_a", password_hash=hash_password("password123"))
        user_b = User(username="user_b", password_hash=hash_password("password123"))
        user_c = User(username="user_c", password_hash=hash_password("password123"))
        session.add_all([user_a, user_b, user_c])
        session.commit()

        emp_a = create_test_employee(session, user_a.id, "User", "A")
        emp_b = create_test_employee(session, user_b.id, "User", "B", supervisor_id=user_a.id)
        emp_c = create_test_employee(session, user_c.id, "User", "C", supervisor_id=user_b.id)
        session.add_all([emp_a, emp_b, emp_c])
        session.commit()

        # Set up hierarchy
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository

        employee_service = EmployeeService(
            EmployeeRepository(session),
            hierarchy_repo,
            UserRepository(session)
        )
        
        for emp in [emp_a, emp_b, emp_c]:
            hierarchy_repo.add_self_reference(emp)
        
        employee_service.assign_supervisor_to_employee(emp_b, emp_a)
        employee_service.assign_supervisor_to_employee(emp_c, emp_b)

        # Delete user B (which should also delete employee and heal hierarchy)
        response = superuser_client.delete(f"/users/{user_b.id}")
        assert response.status_code == 200

        # Verify user B and employee B are deleted
        session.expire_all()
        deleted_user = session.get(User, user_b.id)
        assert deleted_user is None
        deleted_emp = session.get(Employee, user_b.id)
        assert deleted_emp is None

        # Verify C now reports to A
        emp_c_updated = session.get(Employee, user_c.id)
        assert emp_c_updated is not None
        assert emp_c_updated.supervisor_id == user_a.id

        # Verify hierarchy
        ancestors_after = hierarchy_repo.get_ancestor_ids(user_c.id, include_self=False)
        assert user_a.id in ancestors_after
        assert user_b.id not in ancestors_after
