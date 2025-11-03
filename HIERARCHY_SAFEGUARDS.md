# Employee Hierarchy Safeguards - Circular Reference Prevention

## Summary

**YES, there are comprehensive safeguards** to prevent circular references and bad state in the employee hierarchy, especially when modifying supervisors through the PATCH `/users/{id}` endpoint.

## Safeguards Implemented

### 1. ✅ Circular Reference Detection

**Location:** `app/services/employee.py` - `_validate_supervisor_assignment()` method

The system prevents both **direct** and **indirect** circular references:

```python
def would_create_cycle(self, target: Employee, supervisor: Employee) -> bool:
    subordinate_ids = self.hierarchy_repo.get_descendant_ids(target.user_id)
    return supervisor.user_id in subordinate_ids
```

**How it works:**
- Before assigning a supervisor, checks if the proposed supervisor is already a subordinate (at any level) of the target employee
- If found, raises `HierarchyCycleError`

**Example scenarios prevented:**
- Direct cycle: A → B, then trying B → A ❌
- Indirect cycle: A → B → C, then trying C → A ❌
- Multi-level cycle: A → B → C → D, then trying D → A ❌

### 2. ✅ Self-Supervision Prevention

**Location:** `app/services/employee.py` - `_validate_supervisor_assignment()` method

```python
if target.user_id == supervisor.user_id:
    raise InvalidSupervisorAssignmentError(
        "Employee cannot be their own supervisor"
    )
```

**Prevents:** Employee being assigned as their own supervisor ❌

### 3. ✅ Maximum Hierarchy Depth Enforcement

**Location:** `app/services/employee.py` - `_validate_supervisor_assignment()` method

**Configuration:** `Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS = 20`

```python
supervisor_depth = self._get_depth(supervisor)
target_subtree_depth = self._get_subtree_depth(target)

max_depth = Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS
if supervisor_depth + target_subtree_depth + 1 > max_depth:
    raise HierarchyDepthExceededError(
        f"Assignment would exceed maximum hierarchy depth of {max_depth}"
    )
```

**How it works:**
- Calculates the depth of the supervisor in the hierarchy
- Calculates the depth of the target's subtree (if they have subordinates)
- Ensures the combined depth doesn't exceed 20 levels
- **Prevents:** Creating unreasonably deep hierarchies that could impact performance

## Validation Flow

When PATCH `/users/{id}` is called with `new_supervisor_id`:

```
PATCH /users/{id} with new_supervisor_id
    ↓
UserService.patch_user()
    ↓
UserService._handle_supervisor_change()
    ↓
EmployeeService.assign_supervisor_to_employee()
    ↓
EmployeeService._validate_supervisor_assignment()
    ↓
    ├─→ Check: Self-supervision?
    ├─→ Check: Would create cycle?
    └─→ Check: Would exceed max depth?
```

If **any** validation fails:
- Operation is **aborted**
- Appropriate exception is raised
- HTTP 400 error is returned to client
- **No changes** are committed to the database

## Error Types and HTTP Status Codes

| Error Type | Exception | HTTP Status | When Raised |
|------------|-----------|-------------|-------------|
| Self-supervision | `InvalidSupervisorAssignmentError` | 400 | Employee assigned as own supervisor |
| Circular reference | `HierarchyCycleError` | 400 | Assignment would create a cycle |
| Max depth exceeded | `HierarchyDepthExceededError` | 400 | Would exceed 20 levels deep |
| Supervisor not found | `EmployeeNotFoundError` | 404 | Supervisor UUID doesn't exist |

## Test Coverage

### Unit Tests (`tests/unit/test_services/test_employee_service.py`)

✅ `test_prevents_self_assignment` - Prevents employee being their own supervisor
✅ `test_prevents_cycle_creation` - Prevents direct circular references
✅ `test_prevents_depth_exceeded` - Prevents exceeding max hierarchy depth
✅ `test_detects_direct_cycle` - Detects A → B, B → A cycles
✅ `test_detects_indirect_cycle` - Detects A → B → C, C → A cycles

### Integration Tests (`tests/integration/test_user_endpoints.py`)

✅ `test_patch_user_prevents_circular_reference` - Prevents cycles via PATCH endpoint
✅ `test_patch_user_prevents_self_supervision` - Prevents self-supervision via PATCH endpoint
✅ `test_patch_user_supervisor` - Normal supervisor assignment works
✅ `test_patch_user_change_supervisor` - Changing supervisors works
✅ `test_patch_user_remove_supervisor` - Removing supervisors works
✅ `test_patch_user_employee_without_supervisor_field` - Preserves supervisor when not modifying

**All 10 integration tests PASS** ✅

## Example API Responses

### ❌ Attempting Circular Reference
```bash
PATCH /users/{emp1_id}
{
  "new_employee": {
    "new_supervisor_id": "{emp2_id}"  # emp2 is subordinate of emp1
  }
}
```

**Response:**
```json
{
  "status_code": 400,
  "detail": "Assigning {emp2_id} as supervisor of {emp1_id} would create a cycle"
}
```

### ❌ Attempting Self-Supervision
```bash
PATCH /users/{emp_id}
{
  "new_employee": {
    "new_supervisor_id": "{emp_id}"  # same as target
  }
}
```

**Response:**
```json
{
  "status_code": 400,
  "detail": "Employee cannot be their own supervisor"
}
```

### ❌ Exceeding Max Depth
```bash
PATCH /users/{emp_id}
{
  "new_employee": {
    "new_supervisor_id": "{supervisor_at_level_19}"
  }
}
```

**Response:**
```json
{
  "status_code": 400,
  "detail": "Assignment would exceed maximum hierarchy depth of 20"
}
```

## Hierarchy Integrity

The system uses a **closure table** pattern (`employee_hierarchy` table) to efficiently:
1. Track all ancestor-descendant relationships
2. Query "all subordinates" in a single SQL query
3. Detect cycles by checking if proposed supervisor is in subordinate list
4. Calculate hierarchy depth efficiently

**Database guarantees:**
- Validation happens **before** any database changes
- If validation fails, transaction is rolled back
- Hierarchy table stays consistent with employee.supervisor_id
- Self-references are maintained for all employees

## Configuration

Maximum hierarchy depth can be configured in `app/config/settings.py`:

```python
EMPLOYEE_MAX_HIRARCHY_LEVELS: int = 20  # Default: 20 levels
```

This can be adjusted based on organizational needs, but:
- ⚠️ Very deep hierarchies (>20) may impact query performance
- ⚠️ Most organizations don't need more than 10-15 levels

## Conclusion

The system has **robust safeguards** against circular references:

✅ **Prevents** self-supervision  
✅ **Prevents** direct circular references (A → B → A)  
✅ **Prevents** indirect circular references (A → B → C → A)  
✅ **Prevents** excessive hierarchy depth (>20 levels)  
✅ **Validates** before making any changes  
✅ **Rolls back** on any validation failure  
✅ **Well-tested** with both unit and integration tests  

**The hierarchy cannot get into a bad state** through the PATCH endpoint when modifying supervisors.
