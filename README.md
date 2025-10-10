# fs-backend

Minimal FastAPI + SQLModel auth + users service.

## Run
```bash
uv sync
uv run fastapi dev --port 3001 app/main.py
```
App: http://127.0.0.1:3001

## Core Endpoints (MVP)
Auth:
- POST /auth/register → TokenPair (access, refresh)
- POST /auth/login → TokenPair
- POST /auth/refresh → new access token
- POST /auth/logout-all → 204 (rotates user.token_key)
- POST /auth/change-password → 204 (rotates token_key)

Users:
- POST /users → create user (returns UserRead)
- GET  /users → list users (auth required)

## JWT Payload
```
{
	"sub": "<user_id>",
	"key": "<rotating uuid>",
	"kind": "access|refresh",
	"iat": <epoch>,
	"exp": <epoch>
}
```
Rotation: logout-all or password change issues new `key` → all prior tokens invalid.

## Validation Rules
Username: >=4 chars, no spaces.
Password: >=8 chars.

## Error Mapping
Status | Condition
------ | ---------
401 | Invalid credentials / token decode / invalidated token
404 | User not found (lookup by id)
409 | Username already exists
422 | ValidationError (username/password rules)
400 | Other DomainError

Response shape:
```json
{"detail": "Message"}
```

## Notes
- SQLite dev DB auto-created.
- No migrations, tests, or rate limiting (intentional scope reduction).
- Rotating `token_key` is the only token invalidation mechanism.

## License
Internal / TBD
