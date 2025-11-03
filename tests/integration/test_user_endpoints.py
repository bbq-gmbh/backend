"""Integration tests for user endpoints."""


class TestCreateUser:
    """Test POST /users endpoint."""

    def test_create_user_success(self, client):
        """Test successful user creation via API."""
        response = client.post(
            "/users",
            json={"username": "apiuser", "password": "password123"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "apiuser"
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_create_user_duplicate(self, client, created_user):
        """Test creating user with duplicate username."""
        response = client.post(
            "/users",
            json={"username": created_user.username, "password": "password123"},
        )

        assert response.status_code == 409


class TestListUsers:
    """Test GET /users endpoint."""

    def test_list_users_requires_auth(self, client):
        """Test that listing users requires authentication."""
        response = client.get("/users")
        assert (
            response.status_code == 403
        )  # HTTPBearer returns 403 when no auth provided

    def test_list_users_success(self, client, authenticated_client):
        """Test successful user listing."""
        response = authenticated_client.get("/users?page=0&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "page" in data
        assert "total" in data
        assert len(data["page"]) >= 1

        # Verify user data structure
        user_data = data["page"][0]
        assert "id" in user_data
        assert "username" in user_data
        assert "password" not in user_data
        assert "hashed_password" not in user_data

    def test_list_users_invalid_token(self, client):
        """Test listing users with invalid token."""
        response = client.get(
            "/users",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


class TestPatchUser:
    """Test PATCH /users/{id} endpoint."""

    def test_patch_user_requires_auth(self, client, created_user):
        """Test that patching user requires authentication."""
        response = client.patch(
            f"/users/{created_user.id}",
            json={"new_username": "newname"},
        )
        assert response.status_code == 403

    def test_patch_user_requires_superuser(self, client, authenticated_client, created_user):
        """Test that patching user requires superuser."""
        response = authenticated_client.patch(
            f"/users/{created_user.id}",
            json={"new_username": "newname"},
        )
        assert response.status_code == 403

    def test_patch_user_username(self, client, superuser_client, session):
        """Test updating user username."""
        from app.models.user import User
        from app.core.security import hash_password

        test_user = User(
            username="patchtest",
            password_hash=hash_password("password123"),
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

        response = superuser_client.patch(
            f"/users/{test_user.id}",
            json={"new_username": "patchedusertest"},
        )
        assert response.status_code == 200

    def test_patch_user_employee_names(self, client, superuser_client, session):
        """Test updating employee names."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        test_user = User(
            username="empnametest",
            password_hash=hash_password("password123"),
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

        employee = Employee(
            user_id=test_user.id,
            first_name="Original",
            last_name="Name",
        )
        session.add(employee)
        session.commit()
        hierarchy_repo.add_self_reference(employee)

        response = superuser_client.patch(
            f"/users/{test_user.id}",
            json={
                "new_employee": {
                    "new_first_name": "Updated",
                    "new_last_name": "Person",
                }
            },
        )
        assert response.status_code == 200

        # Verify update
        session.refresh(employee)
        assert employee.first_name == "Updated"
        assert employee.last_name == "Person"

    def test_patch_user_supervisor(self, client, superuser_client, session):
        """Test updating employee supervisor."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create supervisor user and employee
        supervisor_user = User(
            username="supervisor",
            password_hash=hash_password("password123"),
        )
        session.add(supervisor_user)
        session.commit()
        session.refresh(supervisor_user)

        supervisor_emp = Employee(
            user_id=supervisor_user.id,
            first_name="Supervisor",
            last_name="Person",
        )
        session.add(supervisor_emp)
        session.commit()
        hierarchy_repo.add_self_reference(supervisor_emp)

        # Create employee user
        emp_user = User(
            username="employee",
            password_hash=hash_password("password123"),
        )
        session.add(emp_user)
        session.commit()
        session.refresh(emp_user)

        employee = Employee(
            user_id=emp_user.id,
            first_name="Employee",
            last_name="Person",
        )
        session.add(employee)
        session.commit()
        hierarchy_repo.add_self_reference(employee)

        # Patch employee to add supervisor
        response = superuser_client.patch(
            f"/users/{emp_user.id}",
            json={
                "new_employee": {
                    "new_supervisor_id": str(supervisor_user.id),
                }
            },
        )
        assert response.status_code == 200

        # Verify supervisor assignment
        session.refresh(employee)
        assert employee.supervisor_id == supervisor_user.id

        # Verify hierarchy was updated
        ancestors = hierarchy_repo.get_ancestor_ids(emp_user.id, include_self=False)
        assert supervisor_user.id in ancestors

    def test_patch_user_change_supervisor(self, client, superuser_client, session):
        """Test changing employee supervisor."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create two supervisors
        super1_user = User(
            username="super1",
            password_hash=hash_password("password123"),
        )
        super2_user = User(
            username="super2",
            password_hash=hash_password("password123"),
        )
        session.add_all([super1_user, super2_user])
        session.commit()

        super1_emp = Employee(
            user_id=super1_user.id,
            first_name="Super1",
            last_name="Person",
        )
        super2_emp = Employee(
            user_id=super2_user.id,
            first_name="Super2",
            last_name="Person",
        )
        session.add_all([super1_emp, super2_emp])
        session.commit()
        hierarchy_repo.add_self_reference(super1_emp)
        hierarchy_repo.add_self_reference(super2_emp)

        # Create employee with first supervisor
        emp_user = User(
            username="changingemployee",
            password_hash=hash_password("password123"),
        )
        session.add(emp_user)
        session.commit()
        session.refresh(emp_user)

        employee = Employee(
            user_id=emp_user.id,
            first_name="Changing",
            last_name="Employee",
            supervisor_id=super1_user.id,
        )
        session.add(employee)
        session.commit()
        hierarchy_repo.add_self_reference(employee)
        
        # Add initial hierarchy paths
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository
        
        employee_service = EmployeeService(
            EmployeeRepository(session), 
            hierarchy_repo, 
            UserRepository(session)
        )
        employee_service.assign_supervisor_to_employee(employee, super1_emp)

        # Change to second supervisor
        response = superuser_client.patch(
            f"/users/{emp_user.id}",
            json={
                "new_employee": {
                    "new_supervisor_id": str(super2_user.id),
                }
            },
        )
        assert response.status_code == 200

        # Verify supervisor changed
        session.refresh(employee)
        assert employee.supervisor_id == super2_user.id

        # Verify hierarchy updated
        ancestors = hierarchy_repo.get_ancestor_ids(emp_user.id, include_self=False)
        assert super2_user.id in ancestors
        assert super1_user.id not in ancestors

    def test_patch_user_remove_supervisor(self, client, superuser_client, session):
        """Test removing employee supervisor (set to None)."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create supervisor
        supervisor_user = User(
            username="suptoremove",
            password_hash=hash_password("password123"),
        )
        session.add(supervisor_user)
        session.commit()
        session.refresh(supervisor_user)

        supervisor_emp = Employee(
            user_id=supervisor_user.id,
            first_name="ToRemove",
            last_name="Supervisor",
        )
        session.add(supervisor_emp)
        session.commit()
        hierarchy_repo.add_self_reference(supervisor_emp)

        # Create employee with supervisor
        emp_user = User(
            username="emptoremove",
            password_hash=hash_password("password123"),
        )
        session.add(emp_user)
        session.commit()
        session.refresh(emp_user)

        employee = Employee(
            user_id=emp_user.id,
            first_name="NoSuper",
            last_name="Employee",
            supervisor_id=supervisor_user.id,
        )
        session.add(employee)
        session.commit()
        hierarchy_repo.add_self_reference(employee)
        
        # Add initial hierarchy
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository
        
        employee_service = EmployeeService(
            EmployeeRepository(session),
            hierarchy_repo,
            UserRepository(session)
        )
        employee_service.assign_supervisor_to_employee(employee, supervisor_emp)

        # Remove supervisor (set to null)
        response = superuser_client.patch(
            f"/users/{emp_user.id}",
            json={
                "new_employee": {
                    "new_supervisor_id": None,
                }
            },
        )
        assert response.status_code == 200

        # Verify supervisor removed
        session.refresh(employee)
        assert employee.supervisor_id is None

        # Verify hierarchy updated (only self-reference should remain)
        ancestors = hierarchy_repo.get_ancestor_ids(emp_user.id, include_self=False)
        assert len(ancestors) == 0

    def test_patch_user_employee_without_supervisor_field(self, client, superuser_client, session):
        """Test that patching employee without new_supervisor_id field doesn't affect existing supervisor."""
        from app.models.user import User
        from app.models.employee import Employee
        from app.core.security import hash_password
        from app.repositories.employee_hierarchy import EmployeeHierarchyRepository

        hierarchy_repo = EmployeeHierarchyRepository(session)

        # Create supervisor
        supervisor_user = User(
            username="unchangedsup",
            password_hash=hash_password("password123"),
        )
        session.add(supervisor_user)
        session.commit()
        session.refresh(supervisor_user)

        supervisor_emp = Employee(
            user_id=supervisor_user.id,
            first_name="Unchanged",
            last_name="Supervisor",
        )
        session.add(supervisor_emp)
        session.commit()
        hierarchy_repo.add_self_reference(supervisor_emp)

        # Create employee with supervisor
        emp_user = User(
            username="empunchangedsup",
            password_hash=hash_password("password123"),
        )
        session.add(emp_user)
        session.commit()
        session.refresh(emp_user)

        employee = Employee(
            user_id=emp_user.id,
            first_name="Employee",
            last_name="WithSupervisor",
            supervisor_id=supervisor_user.id,
        )
        session.add(employee)
        session.commit()
        hierarchy_repo.add_self_reference(employee)
        
        # Add initial hierarchy
        from app.services.employee import EmployeeService
        from app.repositories.employee import EmployeeRepository
        from app.repositories.user import UserRepository
        
        employee_service = EmployeeService(
            EmployeeRepository(session),
            hierarchy_repo,
            UserRepository(session)
        )
        employee_service.assign_supervisor_to_employee(employee, supervisor_emp)

        # Patch employee name WITHOUT touching supervisor
        response = superuser_client.patch(
            f"/users/{emp_user.id}",
            json={
                "new_employee": {
                    "new_first_name": "ChangedName",
                }
            },
        )
        assert response.status_code == 200

        # Verify supervisor is UNCHANGED
        session.refresh(employee)
        assert employee.supervisor_id == supervisor_user.id
        assert employee.first_name == "ChangedName"

        # Verify hierarchy is still intact
        ancestors = hierarchy_repo.get_ancestor_ids(emp_user.id, include_self=False)
        assert supervisor_user.id in ancestors

