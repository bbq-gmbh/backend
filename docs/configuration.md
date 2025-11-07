# Configuration Guide

Environment variables and application configuration for fs-backend.

## Overview

fs-backend uses environment variables for configuration, loaded via `python-dotenv` from a `.env` file (development) or system environment variables (production).

**Configuration Module**: `app/config/settings.py`

---

## Environment Variables

### Database Configuration

| Variable | Required | Default | Type | Description |
|----------|----------|---------|------|-------------|
| `DATABASE_URL` | ✅ Yes | `sqlite:///.temp/database.db` | string | Database connection URL |
| `TESTING` | No | `0` | boolean | Set to `1` to skip .env loading (for tests) |

**DATABASE_URL Format**: `dialect://username:password@host:port/database`

**Examples**:
```env
# SQLite (development)
DATABASE_URL=sqlite:///./dev.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# PostgreSQL with async
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

### Authentication Configuration

| Variable | Required | Default | Type | Description |
|----------|----------|---------|------|-------------|
| `JWT_SECRET_KEY` | ✅ Yes | `test-secret-key-change-in-production` | string | JWT signing secret (min 32 chars) |
| `JWT_ALGORITHM` | No | `HS256` | string | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | integer | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | integer | Refresh token lifetime |

**JWT_SECRET_KEY Requirements**:
- Minimum 32 characters (64+ recommended)
- Cryptographically random
- Never commit to version control
- Different for each environment

**Generate Secure Key**:
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

### Application Configuration

| Variable | Required | Default | Type | Description |
|----------|----------|---------|------|-------------|
| `EMPLOYEE_MAX_HIRARCHY_LEVELS` | No | `20` | integer | Maximum hierarchy depth |
| `TIME_ENTRY_MAX_ENTRIES_PER_DAY` | No | `20` | integer | Max time entries per day |
| `TIME_ENTRY_EDIT_MAX_DAYS` | No | `7` | integer | Days allowed for editing past entries |

---

## Configuration by Environment

### Development

**.env file example**:
```env
# Database (SQLite for simplicity)
DATABASE_URL=sqlite:///./dev.db

# JWT (use test key, will print warning)
JWT_SECRET_KEY=my-super-secret-development-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
EMPLOYEE_MAX_HIRARCHY_LEVELS=20
TIME_ENTRY_MAX_ENTRIES_PER_DAY=20
TIME_ENTRY_EDIT_MAX_DAYS=7
```

**Notes**:
- SQLite database auto-creates on first run
- No migrations needed for development
- Test keys acceptable (but should warn)
- Verbose logging recommended

### Staging

**Environment Variables**:
```bash
export DATABASE_URL="postgresql://stage_user:stage_pass@staging-db.internal:5432/fs_backend_stage"
export JWT_SECRET_KEY="$(openssl rand -base64 32)"
export JWT_ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="20"
export REFRESH_TOKEN_EXPIRE_DAYS="3"
```

**Considerations**:
- Use PostgreSQL for reliability
- Shorter token lifetimes for safety
- SSL required for database connections
- Monitor logs for errors

### Production

**Environment Variables** (via secrets manager):
```bash
export DATABASE_URL="postgresql://prod_user:prod_pass@prod-db.example.com:5432/fs_backend_prod"
export JWT_SECRET_KEY="<64-character cryptographically secure random string>"
export JWT_ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="15"
export REFRESH_TOKEN_EXPIRE_DAYS="7"
export EMPLOYEE_MAX_HIRARCHY_LEVELS="50"
export TIME_ENTRY_MAX_ENTRIES_PER_DAY="30"
export TIME_ENTRY_EDIT_MAX_DAYS="14"
```

**Security Requirements**:
- Store secrets in secure manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- Never commit `.env` to version control
- Use strong JWT_SECRET_KEY (64+ random characters)
- HTTPS/TLS for all connections
- Database SSL connections
- Rate limiting on auth endpoints
- Monitoring and alerting
- Regular secret rotation

---

## Configuration Management

### Development Setup

**Create .env from template**:
```bash
# Option 1: Manual copy
cp .env.template .env
# Edit .env with your values

# Option 2: Quick setup
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET_KEY=dev-key-change-in-production-min-32-chars-required
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF
```

**Verify configuration loads**:
```bash
uv run python -c "from app.config.settings import settings; print(settings.DATABASE_URL)"
```

### Environment-Specific Configurations

**Create environment-specific .env files**:
```
.env                 # Development (git ignored)
.env.staging         # Staging (for reference only, real settings in env vars)
.env.production      # Production (for reference only, real settings in env vars)
```

**Use .env based on context**:
```bash
# Development
python -m uvicorn app.main:app --reload

# Staging (environment variables)
DATABASE_URL=postgresql://... JWT_SECRET_KEY=... python -m uvicorn app.main:app

# Production
# Use container/OS environment variables or secrets manager
docker run -e DATABASE_URL=postgresql://... -e JWT_SECRET_KEY=... app:latest
```

### Using Secrets Manager (Production)

**AWS Secrets Manager Example**:
```bash
#!/bin/bash
# Load secrets from AWS
SECRET=$(aws secretsmanager get-secret-value --secret-id fs-backend-prod --query SecretString --output text)
export DATABASE_URL=$(echo $SECRET | jq -r '.database_url')
export JWT_SECRET_KEY=$(echo $SECRET | jq -r '.jwt_secret_key')
export JWT_ALGORITHM=$(echo $SECRET | jq -r '.jwt_algorithm')

# Run application
uvicorn app.main:app --host 0.0.0.0 --port 3001
```

**Format of secret in AWS**:
```json
{
  "database_url": "postgresql://...",
  "jwt_secret_key": "...",
  "jwt_algorithm": "HS256",
  "access_token_expire_minutes": "15",
  "refresh_token_expire_days": "7"
}
```

---

## Settings Class

**File**: `app/config/settings.py`

**Implementation**:
```python
class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = _get_env("DATABASE_URL", "sqlite:///.temp/database.db")
    
    # JWT
    JWT_SECRET_KEY: str = _get_env("JWT_SECRET_KEY", "test-secret-key...")
    JWT_ALGORITHM: str = _get_env("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(_get_env("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Application
    EMPLOYEE_MAX_HIRARCHY_LEVELS: int = 20
    TIME_ENTRY_MAX_ENTRIES_PER_DAY: int = 20
    TIME_ENTRY_EDIT_MAX_DAYS: int = 7

settings = Settings()
```

**Usage in code**:
```python
from app.config.settings import settings

def configure_database():
    # Access settings
    engine = create_engine(settings.DATABASE_URL)
    return engine

def issue_token(user: User):
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    ...
```

---

## Validation & Error Handling

### Environment Variable Validation

**Invalid Configuration Handling**:
```python
def _get_env(key: str, default: str | None = None) -> str:
    """Gets an environment variable with optional default."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set.")
    return value
```

**Example Error**:
```
ValueError: Environment variable 'JWT_SECRET_KEY' not set.
```

### Type Conversion

**Integer Parsing**:
```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
```

**If conversion fails**:
```
ValueError: invalid literal for int() with base 10: 'invalid'
```

### Best Practices

1. **Always provide sensible defaults** (where appropriate)
2. **Validate on startup** (fail fast if config is invalid)
3. **Log configuration** (but never log secrets)
4. **Type hints** for clarity
5. **Document requirements** in README

---

## Security Checklist

### Development
- [ ] `.env` added to `.gitignore`
- [ ] Use test/dummy values for secrets
- [ ] Never commit real secrets
- [ ] Change defaults if deploying anywhere

### Staging
- [ ] Unique secrets per environment
- [ ] SSL for database connections
- [ ] Audit access to configuration
- [ ] Monitor configuration changes

### Production
- [ ] Secrets stored in secure manager (AWS Secrets Manager, Vault)
- [ ] Strong, random JWT_SECRET_KEY (64+ characters)
- [ ] SSL/TLS for all connections
- [ ] Regular secret rotation policy
- [ ] No hardcoded credentials anywhere
- [ ] Audit logging for configuration access
- [ ] Monitoring and alerting on failed auth
- [ ] Database backups configured
- [ ] Disaster recovery plan

---

## Troubleshooting

### "Environment variable 'JWT_SECRET_KEY' not set"

**Cause**: Missing required environment variable

**Solution**:
```bash
# Check if variable is set
echo $JWT_SECRET_KEY

# Set in current session
export JWT_SECRET_KEY="your-secret-key"

# Or add to .env file
echo "JWT_SECRET_KEY=your-secret-key" >> .env
```

### "DATABASE_URL not recognized"

**Cause**: Invalid connection string format

**Valid Formats**:
```
sqlite:///./dev.db              # SQLite
postgresql://user:pass@host/db  # PostgreSQL
mysql+pymysql://user:pass@host/db  # MySQL
```

**Test Connection**:
```python
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print("Connection successful!")
```

### "Token expiry seems wrong"

**Check Settings**:
```bash
# Print current settings
uv run python -c "from app.config.settings import settings; print(f'Access: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} min, Refresh: {settings.REFRESH_TOKEN_EXPIRE_DAYS} days')"
```

**Verify Token**:
```python
import jwt
from app.config.settings import settings

token = "your_jwt_token"
decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
print(f"Expires: {decoded['exp']}")  # Unix timestamp
```

---

## References

- [Setup Guide - Environment Variables](setup.md#environment-variables-reference)
- [Authentication - Security](authentication.md#security-best-practices)
- [Database - PostgreSQL Setup](database.md)
- [Python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [SQLAlchemy Connection Strings](https://docs.sqlalchemy.org/en/20/core/engines.html)

---

*Last Updated: November 7, 2025*

**Trade-offs**:
- **Shorter**: More secure (less window for stolen token use)
- **Longer**: Better UX (less frequent refresh needed)

**Example**:
```env
# Short-lived for high security
ACCESS_TOKEN_EXPIRE_MINUTES=5

# Balanced (recommended)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Longer for development
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

### REFRESH_TOKEN_EXPIRE_DAYS

**Purpose**: Set refresh token lifetime.

**Default**: `7` days

**Recommendation**:
- Development: 7-30 days
- Production: 7-14 days
- Mobile apps: 30-90 days

**Trade-offs**:
- **Shorter**: More secure but users re-authenticate more often
- **Longer**: Better UX but longer window for stolen token use

**Example**:
```env
# Short-lived
REFRESH_TOKEN_EXPIRE_DAYS=3

# Balanced (recommended)
REFRESH_TOKEN_EXPIRE_DAYS=7

# Longer for mobile apps
REFRESH_TOKEN_EXPIRE_DAYS=30
```

---

### DEBUG

**Purpose**: Enable/disable debug features.

**Values**: `true`, `false`, `1`, `0`, `t`, `f`

**Effects**:
- SQL query logging (echo)
- Detailed error messages
- Development mode behaviors

**Example**:
```env
# Development
DEBUG=true

# Production
DEBUG=false
```

**⚠️ Production Warning**:
- **Always** set `DEBUG=false` in production
- Debug mode may expose sensitive information
- Impacts performance (verbose logging)

---

## .env File Setup

### Create .env File

```bash
# Copy from template
cp .env.template .env

# Edit with your values
nano .env  # or vim, code, etc.
```

### Sample .env File

```env
# Database Configuration
DATABASE_URL=sqlite:///./dev.db

# JWT Configuration
SECRET_KEY=9KvR7X2mP4nL8wQ5tY6uZ3sA1bC0dE7fG9hJ2kM4nP6qR8sT1vW3xY5zA7bC9dE
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
DEBUG=true
```

### .env.template (Committed to Repo)

```env
# Database
DATABASE_URL=sqlite:///./dev.db

# JWT Configuration (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-here-min-32-chars-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
DEBUG=true
```

---

## Loading Configuration

### Settings Module

**File**: `src/config/settings.py`

```python
import os
from typing import Any
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def _get_required_env(key: str) -> str:
    """Get required environment variable or raise error."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value

class Settings:
    # Database
    DATABASE_URL: str = _get_required_env("DATABASE_URL")
    
    # JWT
    SECRET_KEY: str = _get_required_env("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        _get_required_env("ACCESS_TOKEN_EXPIRE_MINUTES")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        _get_required_env("REFRESH_TOKEN_EXPIRE_DAYS")
    )
    
    # Application
    DEBUG: bool = _get_required_env("DEBUG").lower() in ("true", "1", "t")

# Global settings instance
settings = Settings()
```

### Usage

```python
from src.config.settings import settings

# Access configuration
database_url = settings.DATABASE_URL
secret_key = settings.SECRET_KEY
debug_mode = settings.DEBUG
```

---

## Environment-Specific Configuration

### Development

```env
DATABASE_URL=sqlite:///./dev.db
SECRET_KEY=dev-key-not-secure-only-for-local
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
DEBUG=true
```

### Staging

```env
DATABASE_URL=postgresql://user:pass@staging-db:5432/dbname
SECRET_KEY=<strong-unique-staging-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
```

### Production

```env
DATABASE_URL=postgresql://user:pass@prod-db:5432/dbname
SECRET_KEY=<strong-unique-production-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
```

---

## Configuration Best Practices

### Security

1. **Never commit `.env` files**
   - Add `.env` to `.gitignore`
   - Commit `.env.template` instead

2. **Use strong secrets**
   - Generate cryptographically random keys
   - Minimum 32 characters (64+ recommended)
   - Rotate periodically

3. **Separate environments**
   - Different keys per environment (dev/staging/prod)
   - Different database credentials

4. **Restrict access**
   - Limit who can view production secrets
   - Use secret management tools (AWS Secrets Manager, HashiCorp Vault)

### Validation

**Validate on Startup**:

```python
class Settings:
    def __post_init__(self):
        # Validate SECRET_KEY length
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        
        # Validate token expiration
        if self.ACCESS_TOKEN_EXPIRE_MINUTES < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        
        # Warn if using default key
        if "change-in-production" in self.SECRET_KEY.lower():
            if not self.DEBUG:
                raise ValueError("Using default SECRET_KEY in non-debug mode!")
```

---

## Production Deployment

### Docker Environment Variables

**Dockerfile**:
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

# Don't copy .env file!
RUN pip install -r requirements.txt

ENV DEBUG=false

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ACCESS_TOKEN_EXPIRE_MINUTES=15
      - REFRESH_TOKEN_EXPIRE_DAYS=7
      - DEBUG=false
    env_file:
      - .env.production  # Separate production env file (not in repo)
```

### Cloud Platform Environment Variables

**Heroku**:
```bash
heroku config:set SECRET_KEY="<your-key>"
heroku config:set DATABASE_URL="<postgres-url>"
heroku config:set DEBUG=false
```

**AWS Elastic Beanstalk**:
```bash
eb setenv SECRET_KEY="<your-key>" \
         DATABASE_URL="<postgres-url>" \
         DEBUG=false
```

**Railway/Render**:
Set environment variables in dashboard UI.

---

## Troubleshooting

### Missing Environment Variable Error

**Error**:
```
ValueError: Missing required environment variable: SECRET_KEY
```

**Solution**:
1. Ensure `.env` file exists in project root
2. Verify variable is defined: `cat .env | grep SECRET_KEY`
3. Check for typos in variable names
4. Restart application after changes

### Database Connection Error

**Error**:
```
sqlalchemy.exc.OperationalError: unable to open database file
```

**Solution**:
1. Verify `DATABASE_URL` path is correct
2. Ensure directory exists (SQLite creates file, not directory)
3. Check file permissions
4. For PostgreSQL, ensure database exists and credentials are correct

### JWT Decode Error

**Error**:
```
jwt.exceptions.InvalidSignatureError: Signature verification failed
```

**Solution**:
1. Ensure `SECRET_KEY` hasn't changed (invalidates all tokens)
2. Check token was generated with same key
3. Verify key is at least 32 characters

---

## Configuration Reference

### Full Settings Class

```python
class Settings:
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ALGORITHM: str = "HS256"  # JWT algorithm
    
    # Application
    DEBUG: bool
    
    # Future Additions
    # CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    # RATE_LIMIT_PER_MINUTE: int = 100
    # LOG_LEVEL: str = "INFO"
```

---

## References

- [Setup Guide](setup.md) - Initial configuration
- [Authentication](authentication.md) - JWT token configuration
- [Architecture](architecture.md) - Configuration design

---
*Last Updated: October 10, 2025*
