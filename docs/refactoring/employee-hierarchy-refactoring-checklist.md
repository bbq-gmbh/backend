# Employee Hierarchy Refactoring Checklist

## Quick Reference for Refactoring Process

This checklist accompanies the main [Employee Hierarchy Production Spec](../employee-hierarchy-production-spec.md).

---

## ✅ Phase 0: Architectural Refactoring

### Week 1: Foundation

#### Day 1-2: Create New Files
- [ ] Create `app/core/unit_of_work.py`
  - [ ] Implement `UnitOfWork` class
  - [ ] Implement `unit_of_work()` context manager
  - [ ] Add proper type hints
  
- [ ] Create new exception classes in `app/core/exceptions.py`
  - [ ] `HierarchyError` (base class)
  - [ ] `HierarchyCycleError`
  - [ ] `HierarchyDepthExceededError`
  - [ ] `HierarchyCorruptionError`
  - [ ] `InvalidSupervisorAssignmentError`

#### Day 3-4: Refactor Repository Layer
- [ ] Backup current `app/repositories/employee_hierarchy.py`
- [ ] Add new methods to `EmployeeHierarchyRepository` (keep old ones):
  - [ ] `add_self_reference(employee)`
  - [ ] `delete_hierarchy_paths(ancestor_ids, descendant_ids)`
  - [ ] `insert_hierarchy_paths(ancestor_ids, descendant_ids)`
  - [ ] `clear_all_hierarchy()`
  - [ ] `get_ancestor_ids(descendant_id, include_self)`
  - [ ] `get_descendant_ids(ancestor_id, include_self)`
  - [ ] `get_subordinates(supervisor_id, include_self)`
  - [ ] `get_supervisors(subordinate_id, include_self)`
  - [ ] `find_orphaned_employees()`
  - [ ] `get_hierarchy_statistics()`

- [ ] Remove domain logic from repository methods:
  - [ ] Ensure `remove_supervisor()` doesn't set `target.supervisor = None`
  - [ ] Ensure `assign_supervisor()` doesn't set `target.supervisor = X`
  - [ ] Move any validation to service layer

#### Day 5: Write Tests
- [ ] Write unit tests for new repository methods
- [ ] Test with empty database
- [ ] Test with simple hierarchy (2-3 levels)
- [ ] Test edge cases (null values, empty lists)

### Week 2: Service Layer & Dependencies

#### Day 1-2: Refactor Service Layer
- [ ] Backup current `app/services/employee.py`
- [ ] Update `EmployeeService.__init__()`:
  - [ ] Add explicit `user_repo` parameter
  - [ ] Remove `self.session` access
  - [ ] Clean up dependency chain
  
- [ ] Refactor service methods (remove commits):
  - [ ] `create_employee_for_user()` - remove commit
  - [ ] `assign_supervisor_to_employee()` - NEW method with validation
  - [ ] `remove_supervisor_from_employee()` - NEW method
  - [ ] Remove old `assign_supervisor()` (or mark deprecated)
  - [ ] Remove old `remove_supervisor()` (or mark deprecated)

- [ ] Add validation methods:
  - [ ] `_validate_supervisor_assignment()`
  - [ ] `would_create_cycle()`
  - [ ] `_get_depth()`
  - [ ] `_get_subtree_depth()`

- [ ] Add query methods:
  - [ ] `is_supervisor_of()`
  - [ ] `get_hierarchy_level_difference()`

#### Day 3: Update Dependencies
- [ ] Update `app/api/dependencies.py`:
  - [ ] Add `get_unit_of_work()` function
  - [ ] Add `UnitOfWorkDep` type
  - [ ] Update `get_employee_service()` to accept `user_repo`

#### Day 4-5: Write Tests
- [ ] Write unit tests for service methods (mock repositories)
- [ ] Test validation logic
- [ ] Test cycle detection
- [ ] Test depth calculations
- [ ] Test error cases

### Week 3: Migrate Endpoints

#### Day 1: Migrate First Endpoint
- [ ] Choose simple endpoint (e.g., `GET /employees/{user_id}`)
- [ ] Refactor to use `UnitOfWork` pattern
- [ ] Test thoroughly (manual + automated)
- [ ] Verify no regressions

#### Day 2-3: Migrate Write Endpoints
- [ ] Migrate `POST /employees/` (create)
  - [ ] Use UnitOfWork
  - [ ] Call new service methods
  - [ ] Add proper error handling
  - [ ] Commit at endpoint level

- [ ] Migrate supervisor assignment endpoint (if exists)
  - [ ] Use new `assign_supervisor_to_employee()`
  - [ ] Proper transaction management
  - [ ] Error handling

- [ ] Migrate supervisor removal endpoint (if exists)

#### Day 4: Migrate Remaining Endpoints
- [ ] List all employee-related endpoints
- [ ] Migrate each one
- [ ] Test each migration

#### Day 5: Testing & Validation
- [ ] Run full test suite
- [ ] Verify all tests passing
- [ ] Manual testing of all endpoints
- [ ] Check for any regressions

### Week 4: Cleanup & Documentation

#### Day 1-2: Remove Old Code
- [ ] Mark old methods as deprecated (if keeping temporarily)
- [ ] OR remove old methods entirely:
  - [ ] Old `assign_supervisor()` in service
  - [ ] Old `remove_supervisor()` in service
  - [ ] Old repository methods that modified domain
  
- [ ] Remove `self.session` from service layer
- [ ] Remove `self.user_repo` from `EmployeeRepository.__init__()`

#### Day 3: Update Tests
- [ ] Remove tests for deprecated methods
- [ ] Ensure all tests use new patterns
- [ ] Add integration tests for UnitOfWork pattern

#### Day 4: Documentation
- [ ] Update inline code documentation
- [ ] Update API documentation
- [ ] Document transaction management pattern
- [ ] Add examples of proper usage

#### Day 5: Final Review
- [ ] Code review with team
- [ ] Performance testing
- [ ] Security review
- [ ] Deploy to staging

---

## ✅ Phase 1: Critical Features (After Phase 0)

### Week 1-2: Rebuild Functionality

#### Rebuild Implementation
- [ ] Add `rebuild_hierarchy_full()` to repository
- [ ] Add `rebuild_hierarchy()` to service
- [ ] Add `POST /employees/hierarchy/rebuild` endpoint
- [ ] Add proper authentication (admin only)
- [ ] Add rate limiting
- [ ] Write comprehensive tests

#### Partial Rebuild
- [ ] Add `rebuild_hierarchy_subtree()` to repository
- [ ] Add `rebuild_hierarchy_for_employee()` to service
- [ ] Add `POST /employees/hierarchy/rebuild/{user_id}` endpoint
- [ ] Write tests

### Week 2-3: Validation & Integrity

#### Validation Implementation
- [ ] Add `validate_hierarchy()` to repository
- [ ] Add `validate_employee_hierarchy()` to service
- [ ] Add `GET /employees/hierarchy/validate` endpoint
- [ ] Add cycle detection enhancement
- [ ] Add orphan detection
- [ ] Write validation tests

#### Schemas
- [ ] Create `HierarchyValidationReport` schema
- [ ] Create `ValidationIssue` schema
- [ ] Create `HierarchyRebuildReport` schema

---

## ✅ Phase 2: Important Features

### Diagnostics & Monitoring
- [ ] Add statistics methods
- [ ] Add health check endpoint
- [ ] Add hierarchy path visualization
- [ ] Write tests

### Bulk Operations
- [ ] Implement bulk assign supervisor
- [ ] Implement bulk remove supervisors
- [ ] Add proper transaction handling
- [ ] Write tests

---

## ✅ Phase 3: Nice to Have Features

### Advanced Features
- [ ] Hierarchy comparison tools
- [ ] Advanced tree operations
- [ ] Historical tracking
- [ ] Export/import functionality

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] All repository methods tested in isolation
- [ ] All service methods tested with mocked repos
- [ ] All validation logic tested
- [ ] Edge cases covered

### Integration Tests
- [ ] Full rebuild tested
- [ ] Validation workflow tested
- [ ] Error scenarios tested
- [ ] Concurrent access tested

### Performance Tests
- [ ] Rebuild with 1,000 employees
- [ ] Rebuild with 10,000 employees
- [ ] Query performance tested
- [ ] Validation performance tested

---

## 📋 Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed by team
- [ ] Documentation updated
- [ ] API docs updated
- [ ] Database migrations prepared (if any)
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Rollback plan documented
- [ ] Performance benchmarks recorded
- [ ] Security review completed

---

## 🚨 Red Flags to Watch For

During refactoring, if you see any of these, STOP and fix:

- ❌ `session.commit()` in service layer
- ❌ `session.add()` in service layer  
- ❌ Domain model mutations in repository
- ❌ Reaching through dependencies (e.g., `repo.other_repo.session`)
- ❌ Try/except without proper transaction handling
- ❌ Missing validation before hierarchy operations
- ❌ Circular dependencies
- ❌ Tests that don't use mocks for repositories

---

## 📚 Reference Materials

- [Main Specification](../employee-hierarchy-production-spec.md)
- [Closure Table Pattern](https://www.sqlservercentral.com/articles/hierarchies-on-steroids-1-convert-an-adjacency-list-to-nested-sets)
- [Unit of Work Pattern](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

---

## 🎯 Success Criteria

### Phase 0 Complete When:
- ✅ No session management in services
- ✅ No domain logic in repositories
- ✅ All transactions at API layer
- ✅ All existing functionality working
- ✅ All tests passing
- ✅ Code review approved

### Phase 1 Complete When:
- ✅ Rebuild functionality works
- ✅ Validation detects all issues
- ✅ Orphan cleanup works
- ✅ All features tested
- ✅ Documentation complete

### Production Ready When:
- ✅ All phases complete
- ✅ Performance acceptable
- ✅ Monitoring in place
- ✅ Team trained
- ✅ Runbook created
