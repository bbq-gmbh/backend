# fs-backend

Minimal FastAPI + SQLModel auth + users service.

## Quick Start

```bash
# Local development
uv sync
uv run fastapi dev --port 3001 app/main.py

# With Docker Compose (PostgreSQL)
docker compose build
docker compose up

# Run tests
uv sync --all-groups
uv run pytest
```

**App**: http://localhost:3001  
**Docs**: http://localhost:3001/docs

## API Endpoints

**Auth**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with credentials
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout-all` - Invalidate all tokens
- `POST /auth/change-password` - Change password

**Users**
- `POST /users` - Create user
- `GET /users` - List users (requires auth)
