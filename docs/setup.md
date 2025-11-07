# Setup Guide

Complete guide for setting up the fs-backend development environment.

## Prerequisites

### Required Software
- **Python**: 3.13 or higher
- **uv**: Fast Python package installer and resolver ([installation guide](https://github.com/astral-sh/uv))
- **Git**: For version control

### Optional Tools
- **Postman** or **Insomnia**: API testing
- **curl** or **httpie**: Command-line API testing
- **VS Code**: Recommended editor with Python extension

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd backend
```

### 2. Install uv (if not already installed)

**Windows (PowerShell)**:
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Using pip**:
```bash
pip install uv
```

### 3. Install Dependencies

```bash
# Create virtual environment and install dependencies
uv sync
```

This will:
- Create a `.venv` directory
- Install all dependencies from `pyproject.toml`
- Lock dependencies in `uv.lock`

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from template
cp .env.template .env
```

Edit `.env` with your settings:

```env
# Database
DATABASE_URL=sqlite:///./dev.db

# JWT Configuration
SECRET_KEY=your-super-secret-key-min-32-chars-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
DEBUG=true
```

**⚠️ Important**:
- **Never commit `.env` to version control**
- Change `SECRET_KEY` in production (use a secure random string)
- Generate a secure key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

---

## Running the Application

### Development Server

```bash
# Run with FastAPI development server
uv run fastapi dev app/main.py --port 3001
```

**Features**:
- Auto-reload on code changes
- Detailed error messages
- Running at: http://127.0.0.1:3001

### Production Server

```bash
# Using uvicorn with multiple workers
uv run uvicorn app.main:app --host 0.0.0.0 --port 3001 --workers 4
```

### Verify Installation

The server will start and be available at http://127.0.0.1:3001

Access the interactive documentation:
- **Swagger UI**: http://127.0.0.1:3001/docs
- **ReDoc**: http://127.0.0.1:3001/redoc
- **Health Check**: http://127.0.0.1:3001/ (should return 200)

---

## Database Setup

### SQLite (Default - Development)

The SQLite database is **automatically created** on first run:

```bash
# After running the app, you'll see:
./dev.db         # SQLite database file
```

**No migrations needed** for MVP. Schema is created from SQLModel models at startup.

### PostgreSQL (Production - Future)

When ready for production, update `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

Install PostgreSQL driver:
```bash
uv add psycopg2-binary
# or
uv add asyncpg  # for async support
```

---

## Development Workflow

### Project Structure

```
backend/
├── .env                  # Environment variables (DO NOT COMMIT)
├── .env.template         # Environment template
├── .gitignore            # Git ignore rules
├── .python-version       # Python version for uv
├── pyproject.toml        # Project dependencies
├── uv.lock              # Locked dependencies
├── pytest.ini           # Pytest configuration
├── Dockerfile           # Container definition
├── docker-compose.yml   # Docker services
├── coverage.xml         # Coverage report
├── README.md            # Project overview
├── docs/                # Documentation
└── app/                 # Application source
    ├── main.py          # Application entry point
    ├── api/             # API routes
    │   ├── auth.py      # Auth endpoints
    │   ├── users.py     # User endpoints
    │   ├── employees.py # Employee endpoints
    │   ├── time_entries.py   # Time tracking
    │   ├── absence_entries.py # Absence tracking
    │   ├── me.py        # Current user
    │   ├── api.py       # Route registration
    │   ├── dependencies.py    # Dependency injection
    │   ├── setup.py     # Setup endpoints
    │   └── server_store.py    # Server store endpoints
    ├── services/        # Business logic
    │   ├── auth.py      # Authentication service
    │   ├── user.py      # User service
    │   ├── employee.py  # Employee service
    │   ├── setup.py     # Setup service
    │   └── time_entry/  # Time entry services
    ├── repositories/    # Data access
    │   ├── user.py
    │   ├── employee.py
    │   ├── employee_hierarchy.py
    │   ├── time_entry.py
    │   ├── absence_entry.py
    │   └── server_store.py
    ├── models/          # Domain entities
    │   ├── user.py
    │   ├── employee.py
    │   ├── time_entry.py
    │   ├── absence_entry.py
    │   ├── employee_hierarchy.py
    │   └── server_store.py
    ├── schemas/         # DTOs & validation
    │   ├── auth.py
    │   ├── user.py
    │   ├── employee.py
    │   ├── time_entry.py
    │   ├── absence_entry.py
    │   ├── me.py
    │   ├── query.py
    │   ├── setup.py
    │   └── server_store.py
    ├── core/            # Cross-cutting concerns
    │   ├── exceptions.py      # Domain exceptions
    │   ├── security.py        # JWT & password utilities
    │   ├── exception_handlers.py  # Error mapping
    │   └── datetime.py        # Date/time utilities
    └── config/          # Configuration
        ├── settings.py        # Environment settings
        └── database.py        # Database engine & session
├── tests/               # Test suite
    ├── unit/            # Unit tests
    ├── integration/     # Integration tests
    └── fixtures/        # Test data fixtures
```

### Adding Dependencies

```bash
# Add production dependency
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Example: Add pytest
uv add --dev pytest pytest-asyncio
```

### Code Quality Tools

#### Linting and Formatting

```bash
# Install Ruff (recommended)
uv add --dev ruff

# Check for issues
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/
```

#### Type Checking

```bash
# Install mypy
uv add --dev mypy

# Run type checker
uv run mypy src/
```

---

## Interactive API Documentation

Once the server is running, access:

### Swagger UI
**URL**: http://127.0.0.1:3001/docs

**Features**:
- Try out endpoints directly
- See request/response examples
- View schema definitions
- Generate curl commands

### ReDoc
**URL**: http://127.0.0.1:3001/redoc

**Features**:
- Clean, searchable documentation
- Better for reading/reference
- Exportable to PDF/HTML

---

## Testing the API

### Using curl

```bash
# Health check
curl http://127.0.0.1:3001/

# Register a user
curl -X POST http://127.0.0.1:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "password": "SecurePass123!"}'

# Response includes tokens:
# {
#   "access_token": "eyJhbGc...",
#   "refresh_token": "eyJhbGc...",
#   "token_type": "bearer"
# }

# Login
curl -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "password": "SecurePass123!"}'

# Access protected endpoint (replace <token> with actual token)
curl http://127.0.0.1:3001/me \
  -H "Authorization: Bearer <token>"
```

### Using Python with httpx

```python
import httpx

base_url = "http://127.0.0.1:3001"

# Register
response = httpx.post(
    f"{base_url}/auth/register",
    json={"username": "john.doe", "password": "SecurePass123!"}
)
tokens = response.json()
print(f"Access Token: {tokens['access_token']}")

# Use access token for authenticated requests
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
me_response = httpx.get(f"{base_url}/me", headers=headers)
print(me_response.json())
```

---

## Common Issues & Solutions

### Issue: `uv: command not found`
**Solution**: Ensure uv is installed and in your PATH:
```bash
# Verify installation
uv --version

# If not found, reinstall or add to PATH
```

### Issue: `No module named 'src'`
**Solution**: Run commands from the project root, not from `src/`:
```bash
# Wrong: cd src && python main.py
# Correct: uv run fastapi dev src/main.py
```

### Issue: Database locked error
**Solution**: Close all connections to SQLite database:
```bash
# Kill any running server instances
# Delete dev.db and restart
rm dev.db
uv run fastapi dev --port 3001 src/main.py
```

### Issue: Import errors
**Solution**: Ensure you're using the virtual environment:
```bash
# Activate virtual environment manually (if needed)
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Or use uv run prefix
uv run python -c "import fastapi; print('OK')"
```

### Issue: Port already in use
**Solution**: Change port or kill process using port 3001:
```bash
# Windows
netstat -ano | findstr :3001
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:3001 | xargs kill -9

# Or use different port
uv run fastapi dev --port 3002 src/main.py
```

---

## VS Code Setup (Recommended)

### Recommended Extensions

1. **Python** (ms-python.python)
2. **Pylance** (ms-python.vscode-pylance)
3. **Ruff** (charliermarsh.ruff)
4. **REST Client** (humao.rest-client)
5. **SQLite Viewer** (alexcvzz.vscode-sqlite)

### Settings (`.vscode/settings.json`)

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

### Launch Configuration (`.vscode/launch.json`)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: Debug",
      "type": "python",
      "request": "launch",
      "module": "fastapi",
      "args": [
        "dev",
        "--port",
        "3001",
        "src/main.py"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

---

## Next Steps

After setup is complete:

1. ✅ Verify server runs: http://127.0.0.1:3001
2. ✅ Test registration endpoint
3. ✅ Explore Swagger docs: http://127.0.0.1:3001/docs
4. 📖 Read [API Specification](api-spec.md)
5. 📖 Understand [Authentication Flow](authentication.md)
6. 🔨 Start building features!

---

## Getting Help

- **Documentation**: Check `docs/` directory
- **API Docs**: http://127.0.0.1:3001/docs
- **Issues**: Report bugs via GitHub issues
- **Code Review**: Submit pull requests

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./dev.db` | Database connection string |
| `JWT_SECRET_KEY` | Yes | `test-secret-key-change-in-production` | JWT signing key (32+ chars recommended) |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime in days |
| `EMPLOYEE_MAX_HIRARCHY_LEVELS` | No | `20` | Maximum employee hierarchy depth |
| `TIME_ENTRY_MAX_ENTRIES_PER_DAY` | No | `20` | Maximum time entries per day |
| `TIME_ENTRY_EDIT_MAX_DAYS` | No | `7` | Maximum days for editing past entries |

---

## Production Deployment Checklist

When deploying to production:

- [ ] Set `DEBUG=false`
- [ ] Use strong, unique `SECRET_KEY` (32+ characters)
- [ ] Switch to PostgreSQL database
- [ ] Use environment variables, not `.env` file
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Add monitoring/logging
- [ ] Use production WSGI server (uvicorn with workers)
- [ ] Set up database backups
- [ ] Configure firewall rules

---

## References

- [Architecture Overview](architecture.md)
- [API Specification](api-spec.md)
- [Development Guide](development.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---
*Last Updated: November 7, 2025*
