# Refactor Plan

Comprehensive, prioritized refactor plan derived from initial architectural and naming critique. Focus: make layering meaningful, normalize naming, improve security posture, introduce testability, and prepare for growth without premature complexity.

---

## 1. Guiding Principles

1. Each layer must add value (policy, orchestration, invariants) or be removed.
2. Single source of truth for naming and schema contracts.
3. Transaction boundaries owned by service / unit-of-work layer, not repositories.
4. Explicit domain errors mapped centrally to HTTP responses.
5. Security and validation are first-class; no silent fallbacks.
6. Avoid speculative abstractions; delete empty placeholders unless immediately implemented.

---

## 2. Current Layer Assessment

Layer | Issues | Actions
----- | ------ | -------
API Routers | Direct `HTTPException` raising; sync endpoints inside async app (OK short-term). | Introduce exception handlers; keep sync or migrate all async consistently later.
Dependencies (`api/dependencies.py`) | Bloated DI wiring, verbose names, risk of becoming monolith. | Simplify naming; consider lightweight container pattern later.
Services | Mostly pass-through; no transaction orchestration or validation. | Enforce invariants (uniqueness), raise domain errors, own commit control.
Repositories | Commit & refresh internally; no base abstraction but empty `base.py`. | Remove commits; implement optional generic base or delete file.
Models | `validation_key` unclear; `updated_at` onupdate may not behave. | Rename and clarify semantics; verify `onupdate` or switch to server default.
Schemas | Naming inconsistency (`UserCreate` vs `CreateUserRequest`, `UserCreatedResponse`). | Normalize naming scheme.
Auth | Opaque JWT claims (`val`, `kind` literal strings). | Use enums & explicit claim names; add standard claims.
Config | Eager crashing with raw `ValueError`; missing aggregated diagnostics. | Collect missing vars, raise `ConfigurationError` with summary.
Core | `security.py` narrow scope but broad name. | Rename or expand contents.

---

## 3. Naming Normalization Matrix

Category | Current | New | Rationale
-------- | ------- | --- | ---------
User model field | `validation_key` | `token_version` | Semantic clarity: purpose is token invalidation.
JWT claim | `val` | `token_version` (or `ver`) | Align with model; explicit meaning.
JWT claim | `kind` | `token_kind` | Avoid collision with Python built-ins / ambiguity.
Schema (create) | `CreateUserRequest` / `UserCreate` | `UserCreate` | Single canonical input pattern.
Schema (read) | `UserCreatedResponse` | `UserRead` | Standard read/output naming.
Auth method | `create_token_pair` | `issue_token_pair` | Clarifies issuance action.
Auth private method | `_create_token` | `_encode_jwt` | More precise.
UserService method | `invalidate_all_tokens` | `rotate_token_version` | Conveys exact mechanism.
Repository method (get) | `get_user_by_*` | `fetch_by_*` or keep but document | Decide consistent verb (either `get` always returns Optional or switch to `require_*` for raising variant).
Core module | `security.py` | `passwords.py` (or expand) | Reduce implied scope.

Consistency Rules:
- Input schemas: `EntityCreate`, command-like.
- Output schemas: `EntityRead` (or `EntityPublic` if filtered for exposure).
- Avoid mixing tense (`Created`).
- Enum names use explicit domain (`TokenKind`, `TokenType`).

---

## 4. Domain & Error Handling Strategy

Introduce domain exceptions in `core/exceptions.py`:
- `DomainError` (base)
- `UserAlreadyExistsError`
- `UserNotFoundError`
- `InvalidCredentialsError`
- `TokenDecodeError`

Service layer raises these; a global FastAPI exception handler (e.g., `register_exception_handlers(app)`) maps them to structured HTTP responses (409, 404, 401, 400, etc.). Remove scattered `HTTPException` usage from services.

Centralize JWT decode failure reasons (expired, invalid signature, malformed) to enable differentiated logging while still returning generic messages to clients.

---

## 5. Transaction & Persistence Refactor

Problems: Repositories commit per method, preventing multi-entity atomic operations.

Refactor Plan:
1. Remove `session.commit()` and `session.refresh()` from repository methods.
2. Introduce Unit of Work (UoW) pattern (lightweight):
   - `infrastructure/uow.py` (or keep in `repositories/base.py`) with context manager exposing a shared Session.
   - Services obtain UoW via dependency injection and call `uow.commit()` once.
3. Repositories only perform `session.add()` and queries, returning entities.
4. Service orchestrates user creation, uniqueness check, commit, refresh (if needed) in one place.

Incremental Step: Start by moving commit logic into service methods without a full UoW abstraction; introduce formal UoW if/when multi-entity workflows appear.

---

## 6. JWT & Authentication Enhancements

Immediate Changes:
1. Rename claims and integrate enums (`TokenKind`).
2. Add standard claims: `iss`, `aud`, maybe `jti` (for future blacklist support).
3. Replace naive `datetime` objects in payload with UNIX timestamps (ints) for interoperability.
4. Add small clock skew leeway in decode (e.g., `options={'verify_aud': False}` + manual logic) if multi-service deployment expected.
5. Replace `get_token_data` with `decode_token` returning either `TokenData` or raising `TokenDecodeError`.
6. Consider refresh token rotation (on refresh: issue new refresh token and invalidate prior version by incrementing `token_version`). Document if skipping for MVP.

Security Hardening (Next Phase):
- Brute force mitigation: track failed login attempts (in-memory + exponential backoff) or integrate a rate limiter.
- Optional Argon2 over bcrypt if stronger default desired.
- Structured audit logs for auth events (`login_success`, `login_failure`, `token_refresh`, `logout_all`).

---

## 7. Data Validation & Schema Refinement

Add Pydantic validators:
- Username: length (e.g., 3–32), character whitelist.
- Password: minimum length (e.g., 12), optionally entropy or banned list.

Schemas:
- `UserCreate`: username, password.
- `UserRead`: id (UUID), username, created_at, is_active, is_superuser.
- Avoid returning `password_hash` ever; rely on `response_model` filtering.

Handle IntegrityError for duplicate usernames: catch in service, raise `UserAlreadyExistsError` → HTTP 409.

---

## 8. Settings & Configuration Improvements

1. Collect missing environment variables and raise aggregated `ConfigurationError` with list.
2. Introduce optional defaults for non-critical settings (CORS) with override.
3. Add `JWT_ISSUER`, `JWT_AUDIENCE` fields (configurable).
4. Consider namespacing environment variables (e.g., `APP_DEBUG`).
5. Provide a `settings.dump_masked()` method for debugging (mask secrets).

---

## 9. Logging & Observability

Add structured logging (e.g., `structlog` or standard logging with JSON formatter later):
- Log at INFO: successful login, logout-all, token refresh.
- Log at WARN: failed login, invalid token decode reason.
- Include correlation id (future) for tracing.

Expose health/status endpoint in future (`/healthz`) returning app version and simple DB connectivity check.

---

## 10. Testing Strategy (Deferred by Scope Decision)

Per explicit scope: no unit/integration tests will be implemented now. This increases risk of regressions during refactor. Mitigation steps WITHOUT a test harness:
- Perform manual smoke checks after each phase (register, login, protected route, refresh, logout-all).
- Use temporary debug logging to verify token_version rotation and claim structure.
- Keep changes incremental (commit after each logical rename/refactor).

If tests are later reintroduced, resurrect the previously proposed strategy (see history) focusing first on auth flows and repository side-effects.

---

## 11. Migration & Deployment Considerations (Simplified Scope)

Per scope: no Alembic / migration scripts. We will continue using `User.metadata.create_all(engine)` at startup.

Implications:
- Destructive / incompatible schema changes (e.g., renaming `validation_key` → `token_version`) will DROP DATA if done manually in a real persistent environment. Acceptable only if environment is disposable.
- Document any manual DB reset requirement in README after refactor.

Minimal Enhancement (still allowed): Add an environment guard so automatic schema creation only occurs when `AUTO_CREATE_SCHEMA=true` to avoid accidental prod mutations (optional).

---

## 12. Step-by-Step Refactor Plan (Execution Order)

Phase 1 (Low Risk, High Clarity):
1. Normalize schema naming (`UserCreate`, `UserRead`).
2. Rename `validation_key` → `token_version` in model (new column; migration) and code references.
3. Adjust JWT payload + `TokenData` schema fields (`token_version`, `token_kind`).
4. Update AuthService naming (`issue_token_pair`, `_encode_jwt`).
5. Update dependencies to use new decode function and enums.

Phase 2 (Behavioral Hardening):
6. Introduce domain exceptions + global exception handlers.
7. Move commit logic from repository to service (remove commits from `UserRepository`).
8. Add uniqueness handling + raise `UserAlreadyExistsError`.
9. Add validation logic to `UserCreate` (username/password constraints).
10. Add logging events for auth flows.

Phase 3 (Security & Token Evolution):
11. Optional: Implement refresh token rotation (increment token_version on refresh) OR document decision not to.
12. Add `iss`, `aud`, `jti` claims; validate on decode.
13. Expose configuration for token audiences.

Phase 4 (Operational Maturity – Adjusted):
14. Aggregate missing env var errors.
15. Improve `updated_at` handling (SQLAlchemy `func.now()` on update or event listener).
16. Remove or implement `repositories/base.py`; if implemented, generic CRUD base.
17. Document architecture in `README` / `ARCHITECTURE.md`.

Phase 5 (Optional Hardening – Still Within Scope Constraints):
18. (Optional) Add basic structured logging configuration.
19. (Optional) Introduce simple configuration dump (masked) for debugging.

---

## 13. Risk & Rollback Notes

Change | Risk | Mitigation / Rollback
------ | ---- | ---------------------
Renaming model field | Data loss (no migrations) | Accept data reset; clearly document manual DB wipe step.
JWT claim rename | Existing tokens invalidated | Communicate deploy window; optionally accept legacy claim names temporarily.
Commit logic relocation | Hidden dependency on side-effects | Manual smoke test flows immediately after change.
Refresh rotation (if added) | Client code assumptions break | Document in README; bump minor version.

Transitional Strategy for JWT claims (optional): support both `val` and `token_version` for one iteration, logging legacy usage.

---

## 14. Sample Code Adjustments (Illustrative)

Model excerpt:
```python
class User(SQLModel, table=True):
	id: UUID = Field(default_factory=uuid4, primary_key=True)
	username: str = Field(unique=True, index=True)
	password_hash: str
	token_version: int = Field(default=1, index=True)
```

Auth service encode (simplified):
```python
def _encode_jwt(self, user: User, ttl: timedelta, kind: TokenKind) -> str:
	now = datetime.now(timezone.utc)
	payload = {
		"sub": str(user.id),
		"token_version": user.token_version,
		"token_kind": kind.value,
		"iat": int(now.timestamp()),
		"exp": int((now + ttl).timestamp()),
		"iss": settings.JWT_ISSUER,
		"aud": settings.JWT_AUDIENCE,
	}
	return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
```

Exception mapping example:
```python
@app.exception_handler(UserAlreadyExistsError)
async def user_exists_handler(_, exc):
	return JSONResponse(status_code=409, content={"detail": str(exc)})
```

---

## 15. Open Questions / Decisions Needed

1. Will refresh rotation be required now or deferred? (Impacts token schema & user experience.)
2. Is multi-database / sharding ever expected (affects early decision on UoW abstraction design)?
3. Do we need multi-tenant support (prefix claims with tenant id)?
4. Logging format preference (plain vs structured JSON)?
5. Minimum password policy (length only vs complexity/entropy)?

Document answers before Phase 3.

---

## 16. Success Criteria

After refactor:
- All naming matches matrix; no stray legacy identifiers.
- Services contain business rules (uniqueness, validation, revocation) and own transaction commits.
- Repositories side-effect free (no commits). 
- JWT decode path produces structured errors; tests cover positives and negatives.
- Duplicate registration yields HTTP 409 with consistent error payload.
- Test suite covers core flows; all green in CI.
- README updated to reflect architecture & security model.

---

## 17. Follow-Up (Future Enhancements – Explicitly Out of Current Scope)

Out-of-scope per product decision (do NOT implement now):
- OAuth / SSO integration.
- API versioning.
- Formal test suite.
- Migration framework (Alembic) / schema versioning.
- Rate limiting.
- Persistent refresh token storage or replay detection.

Potential future (when scope expands):
- Role / permission system (RBAC).
- Metrics (Prometheus) for auth events.
- OpenAPI security doc enrichment.
- Token reuse detection (would then require storage or jti blacklist).

---

## 18. Execution Checklist (Condensed)

Ordered actionable list for tracking (aligned with reduced scope):
1. Rename fields & schemas (model + JWT claims) – accept data reset.
2. Adjust AuthService & dependencies to new naming.
3. Add domain exceptions + handlers.
4. Move commit logic to services; strip from repositories.
5. Add uniqueness & validation logic (manual verification only).
6. Implement logging for auth events (basic stdout acceptable).
7. Update documentation (reflect no migrations/tests/ratelimiting).
8. Optional: refresh rotation + claim enrichment (without token storage).
9. Optional: environment variable aggregation + structured logging.

---

### Documentation Notes (Pending README Update)

- Schema change: `validation_key` replaced by `token_version` (int, starts at 1). Existing tokens issued prior to refactor are invalid.
- JWT payload claim changes: `val`→`token_version`, `kind`→`token_kind`.
- Method renames in AuthService and UserService; external API unchanged except for registration/login responses still returning token pair.
- Manual DB reset required after refactor if persistent storage was previously used (no migration layer in scope).
- Removed `is_active` field from `User` model and `UserRead` schema (not used; deactivation semantics out of scope). Requires database file recreation for SQLite.

---

This document is the authoritative reference for the refactor scope. Update sections with actual migration IDs, decisions, and test coverage notes as changes land.

