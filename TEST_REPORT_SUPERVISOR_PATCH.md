# PATCH `/users/{id}` - `new_supervisor_id` Test Report

## Summary
The PATCH `/users/{id}` endpoint works **correctly** when handling the `new_supervisor_id` field. All tests pass successfully.

## Test Results

### All Tests Passed ✓
```
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_requires_auth PASSED                    [ 12%]
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_requires_superuser PASSED               [ 25%]
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_username PASSED                         [ 37%]
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_employee_names PASSED                   [ 50%]
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_supervisor PASSED                       [ 62%]
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_change_supervisor PASSED                [ 75%]
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_remove_supervisor PASSED                [ 87%]
tests/integration/test_user_endpoints.py::TestPatchUser::test_patch_user_employee_without_supervisor_field PASSED [100%]
```

## Tested Scenarios

### 1. ✅ Assigning a Supervisor
**Test:** `test_patch_user_supervisor`
- Creates an employee without a supervisor
- Assigns a supervisor via PATCH request
- Verifies supervisor_id is set correctly
- Verifies employee hierarchy is updated

**Request:**
```json
{
  "new_employee": {
    "new_supervisor_id": "d6604caf-3665-4021-8ebe-6df5af0c25af"
  }
}
```

### 2. ✅ Changing a Supervisor
**Test:** `test_patch_user_change_supervisor`
- Creates an employee with Supervisor A
- Changes to Supervisor B via PATCH request
- Verifies supervisor_id is updated
- Verifies hierarchy is correctly updated (old supervisor removed, new one added)

**Request:**
```json
{
  "new_employee": {
    "new_supervisor_id": "0c13c05b-86f9-4161-88ae-b997d3880999"
  }
}
```

### 3. ✅ Removing a Supervisor
**Test:** `test_patch_user_remove_supervisor`
- Creates an employee with a supervisor
- Removes supervisor by setting to `null`
- Verifies supervisor_id is set to None
- Verifies hierarchy paths are removed (only self-reference remains)

**Request:**
```json
{
  "new_employee": {
    "new_supervisor_id": null
  }
}
```

### 4. ✅ Patching Without Touching Supervisor
**Test:** `test_patch_user_employee_without_supervisor_field`
- Creates an employee with a supervisor
- Patches other fields (e.g., first_name) WITHOUT including new_supervisor_id
- Verifies supervisor remains unchanged
- Verifies hierarchy remains intact

**Request:**
```json
{
  "new_employee": {
    "new_first_name": "ChangedName"
  }
}
```

## Implementation Details

### Key Code Section (`app/services/user.py`)

```python
if user_patch.new_employee and user.employee:
    if user_patch.new_employee.new_first_name:
        user.employee.first_name = user_patch.new_employee.new_first_name
    if user_patch.new_employee.new_last_name:
        user.employee.last_name = user_patch.new_employee.new_last_name
    
    # Handle supervisor change - check if field was provided at all
    # We check model_fields_set to distinguish between "not provided" and "provided as None"
    if 'new_supervisor_id' in user_patch.new_employee.model_fields_set:
        self._handle_supervisor_change(
            user.employee, 
            user_patch.new_employee.new_supervisor_id
        )
```

### The `model_fields_set` Approach

The implementation uses Pydantic's `model_fields_set` to distinguish between:
1. **Field not provided** - Supervisor should remain unchanged
2. **Field provided as `null`** - Supervisor should be removed
3. **Field provided with a UUID** - Supervisor should be updated

**Verification Test Results:**
```
=== Test 1: new_supervisor_id explicitly set to None ===
'new_supervisor_id' in model_fields_set: True
new_supervisor_id value: None

=== Test 2: new_supervisor_id not provided ===
'new_supervisor_id' in model_fields_set: False
new_supervisor_id value: None

=== Test 3: new_supervisor_id set to a UUID ===
'new_supervisor_id' in model_fields_set: True
new_supervisor_id value: f00681d8-5c76-4ea3-a47f-c78df5eb12de
```

This proves the approach correctly handles all three cases.

### Hierarchy Management

The `_handle_supervisor_change` method properly:
- Validates the new supervisor exists
- Removes old hierarchy paths when changing supervisors
- Adds new hierarchy paths
- Handles removal (None) by only removing paths without adding new ones

```python
def _handle_supervisor_change(self, employee: Employee, new_supervisor_id: Optional[uuid.UUID]):
    """Handle changing an employee's supervisor with hierarchy updates."""
    if not self.employee_repo or not self.hierarchy_repo:
        raise ValidationError("Employee repository and hierarchy repository required")
    
    employee_service = EmployeeService(
        employee_repo=self.employee_repo,
        employee_hierarchy_repo=self.hierarchy_repo,
        user_repo=self.user_repo
    )
    
    if new_supervisor_id:
        new_supervisor = self.employee_repo.get_employee_by_user_id(new_supervisor_id)
        if not new_supervisor:
            raise EmployeeNotFoundError(user_id=new_supervisor_id)
        
        # Remove old supervisor if exists
        if employee.supervisor_id:
            employee_service.remove_supervisor_from_employee(employee)
        
        # Assign new supervisor
        employee_service.assign_supervisor_to_employee(employee, new_supervisor)
    else:
        # Remove supervisor (set to None)
        if employee.supervisor_id:
            employee_service.remove_supervisor_from_employee(employee)
```

## Dependency Injection

The UserService receives the required repositories via FastAPI dependencies:

```python
def get_user_service(
    user_repo: UserRepositoryDep,
    employee_repo: EmployeeRepositoryDep,
    hierarchy_repo: EmployeeHierarchyRepositoryDep,
) -> UserService:
    return UserService(
        user_repo=user_repo,
        employee_repo=employee_repo,
        hierarchy_repo=hierarchy_repo
    )
```

## Conclusion

The `new_supervisor_id` functionality in the PATCH `/users/{id}` endpoint is **working reliably**:
- ✅ All 8 integration tests pass
- ✅ Correctly distinguishes between "not provided" and "provided as null"
- ✅ Properly updates employee hierarchy
- ✅ Handles supervisor assignment, changes, and removal
- ✅ Preserves supervisor when field is not included in patch

If you're experiencing issues in production/manual testing:
1. Ensure the request includes `new_employee` wrapper
2. Verify the supervisor's UUID is valid and the user has an employee record
3. Check that proper authentication (superuser) is provided
4. Examine server logs for any exceptions

## Additional Test Script

A manual test script has been created at `test_model_fields_set.py` that can be run to verify the Pydantic behavior independently.
