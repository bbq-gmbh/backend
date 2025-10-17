# fs-backend

![Tests](https://github.com/bbq-gmbh/backend/actions/workflows/test.yml/badge.svg?branch=main)

Minimal FastAPI + SQLModel auth + users service.

## Quick Start

```bash
# Local development
uv sync
uv run fastapi dev --port 3001 app/main.py

# With Docker Compose (PostgreSQL)
docker compose build
docker compose up

# Run tests (no .env required!)
uv sync --all-groups
uv run pytest

# Run tests with coverage
uv run pytest -v --cov=app --cov-report=term-missing
```

**App**: http://localhost:3001  
**Docs**: http://localhost:3001/docs

## CI/CD

GitHub Actions automatically run tests on:
- ✅ Push to `main` branch
- ✅ Pull requests to `main`
- ✅ Manual trigger (Actions tab → Tests → Run workflow)

**85% code coverage** • No external dependencies • No `.env` file needed

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
