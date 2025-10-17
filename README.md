# fs-backend

![Tests](https://github.com/bbq-gmbh/backend/actions/workflows/test.yml/badge.svg?branch=main)
![Docker](https://github.com/bbq-gmbh/backend/actions/workflows/docker.yml/badge.svg?branch=main)

Minimal FastAPI + SQLModel auth + users service.

## Quick Start

```bash
# Run with pre-built Docker image
docker run -p 3001:3001 ghcr.io/bbq-gmbh/backend:latest

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

## 🐳 Docker Images

Pre-built images published to GHCR:
- **Latest**: `ghcr.io/bbq-gmbh/backend:latest`
- **Versions**: `ghcr.io/bbq-gmbh/backend:v1.0.0`

See [Docker Publishing Guide](.github/workflows/DOCKER.md) for details.

## CI/CD

GitHub Actions automatically:
- ✅ **Run tests** on push to `main` and PRs
- ✅ **Build & push Docker images** on push to `main` and version tags
- ✅ Manual trigger available in Actions tab

**86% code coverage** • No external dependencies • No `.env` file needed

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
