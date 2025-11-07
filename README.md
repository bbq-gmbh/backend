# fs-backend

![Tests](https://github.com/bbq-gmbh/backend/actions/workflows/test.yml/badge.svg?branch=main)
![Docker](https://github.com/bbq-gmbh/backend/actions/workflows/docker.yml/badge.svg?branch=main)

A robust, production-ready FastAPI-based backend for employee time tracking and management with JWT authentication, role-based access control, and employee hierarchy support.

## 🌟 Features

### Authentication & Authorization
- **JWT-based Authentication**: Stateless authentication using JSON Web Tokens
- **Token Rotation**: Secure token invalidation mechanism without Redis dependency
- **Multi-device Logout**: Invalidate all sessions across devices
- **Password Management**: Secure password hashing with bcrypt and change operations
- **Role-based Access Control (RBAC)**: Superuser and employee-level authorization

### Employee Management
- **Employee Hierarchy**: Multi-level supervisor-subordinate relationships
- **Profile Management**: First name, last name, birthday, hour model, and more
- **Supervisor Permissions**: Supervisors can manage subordinates within hierarchy

### Time & Absence Tracking
- **Time Entries**: Track arrival and departure times
- **Absence Management**: Support for sickness, vacation, and other absence types
- **Date Range Support**: Query entries by date or date range
- **Authorization Controls**: Different permissions based on user roles and hierarchy

### User Management
- **User CRUD**: Create, read, update, delete users
- **Employee Association**: Link users to employee profiles
- **Search Functionality**: Full username search with pagination
- **Superuser Capabilities**: Administrative operations

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | ≥0.121.0 |
| **ORM/Schemas** | SQLModel | ≥0.0.27 |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Latest |
| **Authentication** | PyJWT + bcrypt | ≥2.10.1 / ≥5.0.0 |
| **Python** | Python | ≥3.13 |
| **Package Manager** | uv | Latest |
| **Testing** | pytest + pytest-cov | Latest |

## 🚀 Quick Start

### Prerequisites
- **Python** 3.13 or higher
- **uv** package manager ([install guide](https://docs.astral.sh/uv/getting-started/))
- **Git**

### Installation & Running

```bash
# Clone and install
git clone <repository-url>
cd backend
uv sync

# Create environment configuration
cp .env.template .env

# Start development server
uv run fastapi dev app/main.py --port 3001
```

**Access Points**:
- **API**: http://localhost:3001
- **Docs**: http://localhost:3001/docs
- **ReDoc**: http://localhost:3001/redoc

## 🐳 Docker

### Run with Pre-built Image
```bash
docker run -p 3001:3001 ghcr.io/bbq-gmbh/backend:latest
```

### With Docker Compose
```bash
docker compose build
docker compose up
```

## 🧪 Testing

```bash
# Run all tests
uv sync --all-groups
uv run pytest

# With coverage
uv run pytest -v --cov=app --cov-report=html
```

**Coverage**: 86% code coverage across the project

## 🔐 Authentication Example

```bash
# Register
curl -X POST http://localhost:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "password": "SecurePass123!"}'

# Login
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "password": "SecurePass123!"}'

# Access protected endpoint
curl http://localhost:3001/me \
  -H "Authorization: Bearer <access_token>"
```

## � Documentation

Full documentation in the `/docs` directory:

| Document | Purpose |
|----------|---------|
| [Setup Guide](docs/setup.md) | Installation and environment setup |
| [Architecture](docs/architecture.md) | System design and layered architecture |
| [Authentication](docs/authentication.md) | JWT flows and security details |
| [API Specification](docs/api-spec.md) | Complete endpoint reference |
| [Database Schema](docs/database.md) | Data models and relationships |
| [Configuration](docs/configuration.md) | Environment variables |
| [Error Handling](docs/errors.md) | Error codes and formats |
| [Development](docs/development.md) | Contributing guidelines |

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── repositories/        # Data access
│   ├── models/              # Domain entities
│   ├── schemas/             # DTOs & validation
│   ├── core/                # Security & exceptions
│   └── config/              # Configuration
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

## 🔒 Security

- ✅ **bcrypt** password hashing with salt
- ✅ **JWT** with rotating token versions
- ✅ **Role-based access control** (RBAC)
- ✅ **Parameterized queries** prevent SQL injection
- ✅ **Token invalidation** without Redis

## 🤝 Contributing

1. Create feature branch from `dev`
2. Add tests and ensure coverage
3. Run `pytest` and code quality checks
4. Submit PR with description

See [Development Guide](docs/development.md) for details.

## 📋 API Endpoints

**Auth**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with credentials
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout-all` - Invalidate all tokens
- `POST /auth/change-password` - Change password

**Users**
- `POST /users` - Create user
- `GET /users` - List users (requires auth)
