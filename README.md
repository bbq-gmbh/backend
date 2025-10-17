# fs-backend

Minimal FastAPI + SQLModel auth + users service.

## Run

### Local Development
```bash
uv sync
uv run fastapi dev --port 3001 app/main.py
```
App: http://127.0.0.1:3001

### Docker
```bash
# Build the image
docker build -t fs-backend .

# Run with environment file
docker run -p 3001:3001 -v $(pwd)/.env:/app/.env fs-backend

# Or run with environment variables
docker run -p 3001:3001 \
  -e DATABASE_URL="sqlite:///.temp/database.db" \
  -e JWT_SECRET_KEY="secret" \
  -e JWT_ALGORITHM="HS256" \
  -e ACCESS_TOKEN_EXPIRE_MINUTES="30" \
  -e REFRESH_TOKEN_EXPIRE_DAYS="7" \
  fs-backend
```
App: http://127.0.0.1:3001

### Docker Compose (with PostgreSQL)
```bash
# Build the images
docker compose build

# Start both backend and PostgreSQL
docker compose up

# Or run in background
docker compose up -d

# Stop services
docker compose down

# Stop and remove volumes (deletes database)
docker compose down -v
```
App: http://127.0.0.1:3001

The PostgreSQL database will be accessible at `localhost:5432` with credentials:
- User: `postgres`
- Password: `postgres`
- Database: `fsbackend`


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
