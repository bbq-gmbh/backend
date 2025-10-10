# Configuration Guide

Environment variables and application configuration for fs-backend.

## Overview

fs-backend uses environment variables for configuration, loaded via `python-dotenv` from a `.env` file.

**Configuration File**: `src/config/settings.py`

---

## Environment Variables

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `DATABASE_URL` | string | Database connection string | `sqlite:///./dev.db` |
| `SECRET_KEY` | string | JWT signing key (32+ chars) | `your-secret-key-min-32-chars...` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | Access token lifetime (minutes) | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | integer | Refresh token lifetime (days) | `7` |
| `DEBUG` | boolean | Enable debug mode | `true` or `false` |

---

## Configuration Details

### DATABASE_URL

**Purpose**: Specify database connection.

**Format**: `dialect://username:password@host:port/database`

**Examples**:

```env
# SQLite (development)
DATABASE_URL=sqlite:///./dev.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# PostgreSQL with async support
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

**Notes**:
- SQLite uses relative path: `./dev.db` creates file in project root
- PostgreSQL requires database to exist before running app
- Use connection pooling settings for production

---

### SECRET_KEY

**Purpose**: Sign and verify JWT tokens.

**Requirements**:
- Minimum 32 characters (recommended 64+)
- Cryptographically random
- **Never commit to version control**

**Generate Secure Key**:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32

# Using PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

**Example**:
```env
SECRET_KEY=9KvR7X2mP4nL8wQ5tY6uZ3sA1bC0dE7fG9hJ2kM4nP6qR8sT1vW3xY5zA7bC9dE
```

**⚠️ Security Warning**:
- Change default key immediately
- Use different keys for dev/staging/production
- Rotate keys periodically
- If key is compromised, all tokens become invalid upon rotation

---

### ACCESS_TOKEN_EXPIRE_MINUTES

**Purpose**: Set access token lifetime.

**Default**: `15` minutes

**Recommendation**:
- Development: 15-60 minutes
- Production: 15-30 minutes
- Higher security needs: 5-15 minutes

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
