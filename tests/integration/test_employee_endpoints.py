"""Integration tests for employee endpoints - hierarchy and rebuild."""


class TestGetEmployeeHierarchy:
    """Test GET /employees/hierarchy endpoint."""

    def test_get_hierarchy_requires_auth(self, client):
        """Test that getting hierarchy requires authentication."""
        import uuid
        test_user_id = str(uuid.uuid4())
        response = client.get(f"/employees/{test_user_id}/hierarchy")
        assert response.status_code == 403

    def test_get_own_hierarchy_as_employee(
        self, client, authenticated_client, created_user, session
    ):
        """Test getting own hierarchy as an employee user."""
        from tests.fixtures.user_fixtures import create_test_employee
        # Create an employee for the user using the helper
        create_test_employee(session, created_user.id, "Test", "Employee")
        session.commit()

        # Get hierarchy
        response = authenticated_client.get(f"/employees/{created_user.id}/hierarchy")
        assert response.status_code == 200

        data = response.json()
        assert "employee" in data
        assert "supervisors" in data
        assert "subordinates" in data
        assert data["employee"]["user_id"] == str(created_user.id)
        assert data["employee"]["first_name"] == "Test"
        assert len(data["supervisors"]) == 0  # No supervisor assigned
        assert len(data["subordinates"]) == 0  # No subordinates

    def test_get_hierarchy_of_other_user_as_superuser(
        self, client, superuser_client, session
    ):
        """Test superuser can get hierarchy of any user."""
        # Create a test user with employee
        from app.models.user import User
        from app.core.security import hash_password
        from tests.fixtures.user_fixtures import create_test_employee

        test_user = User(
            username="hierarchytest",
            password_hash=hash_password("password123"),
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

        create_test_employee(session, test_user.id, "Hierarchy", "Test")
        session.commit()

        # Superuser gets this user's hierarchy
        response = superuser_client.get(
            f"/employees/{test_user.id}/hierarchy"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["employee"]["user_id"] == str(test_user.id)
        assert data["employee"]["first_name"] == "Hierarchy"

    def test_get_hierarchy_unauthorized(self, client, authenticated_client, session):
        """Test non-superuser cannot get other user's hierarchy."""
        # Create another user with employee
        from app.models.user import User
        from app.core.security import hash_password
        from tests.fixtures.user_fixtures import create_test_employee

        other_user = User(
            username="otheruser",
            password_hash=hash_password("password123"),
        )
        session.add(other_user)
        session.commit()
        session.refresh(other_user)

        create_test_employee(session, other_user.id, "Other", "User")

        # Try to get other user's hierarchy (should fail)
        response = authenticated_client.get(
            f"/employees/{other_user.id}/hierarchy"
        )
        assert response.status_code == 403


class TestRebuildHierarchy:
    """Test POST /employees/__rebuild_hierarchy endpoint."""

    def test_rebuild_hierarchy_requires_auth(self, client):
        """Test that rebuild hierarchy requires authentication."""
        response = client.post("/employees/__rebuild_hierarchy")
        assert response.status_code == 403

    def test_rebuild_hierarchy_requires_superuser(self, client, authenticated_client):
        """Test that rebuild hierarchy requires superuser."""
        response = authenticated_client.post("/employees/__rebuild_hierarchy")
        assert response.status_code == 403  # UserNotAuthorizedError

    def test_rebuild_hierarchy_success(self, client, superuser_client, session):
        """Test successful hierarchy rebuild."""
        # Create a hierarchy of employees
        from app.models.user import User
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository
        from tests.fixtures.user_fixtures import create_test_employee

        # Initialize hierarchy repo
        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create users
        boss = User(username="boss", password_hash=hash_password("password123"))
        manager = User(username="manager", password_hash=hash_password("password123"))
        worker = User(username="worker", password_hash=hash_password("password123"))

        session.add_all([boss, manager, worker])
        session.commit()

        # Create employees with hierarchy
        boss_emp = create_test_employee(session, boss.id, "Boss", "Person")
        session.commit()
        hierarchy_repo.add_self_reference(boss_emp)

        manager_emp = create_test_employee(session, manager.id, "Manager", "Person", supervisor_id=boss.id)
        session.commit()
        hierarchy_repo.add_self_reference(manager_emp)

        worker_emp = create_test_employee(session, worker.id, "Worker", "Person", supervisor_id=manager.id)
        session.commit()
        hierarchy_repo.add_self_reference(worker_emp)

        # Rebuild hierarchy
        response = superuser_client.post("/employees/__rebuild_hierarchy")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "stats" in data
        assert data["stats"]["employees_processed"] >= 3
        assert data["stats"]["records_created"] > 0

    def test_rebuild_hierarchy_with_force(self, client, superuser_client):
        """Test hierarchy rebuild with force parameter."""
        response = superuser_client.post("/employees/__rebuild_hierarchy?force=true")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "stats" in data
