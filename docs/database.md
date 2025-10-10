# Database Schema

Database schema documentation for fs-backend.

## Overview

**Database Type**: SQLite (development), PostgreSQL-ready  
**ORM**: SQLModel (combines Pydantic + SQLAlchemy)  
**Schema Management**: Auto-created on startup (no migrations for MVP)

---

## Entity Relationship Diagram

```
┌─────────────────────────┐
│         User            │
├─────────────────────────┤
│ id (PK)                 │ UUID
│ username (UNIQUE)       │ String
│ hashed_password         │ String
│ token_version           │ UUID
│ created_at              │ DateTime
│ updated_at              │ DateTime
└─────────────────────────┘

┌─────────────────────────┐
│       Employee          │  (Future use)
├─────────────────────────┤
│ id (PK)                 │ UUID
│ user_id (FK)            │ UUID → User.id
│ first_name              │ String
│ last_name               │ String
│ ...                     │
└─────────────────────────┘
```

---

## Tables

### Users Table

**Table Name**: `users`

**Purpose**: Store user accounts for authentication and identification.

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique user identifier |
| `username` | VARCHAR(255) | NOT NULL, UNIQUE | User's login name |
| `hashed_password` | VARCHAR(255) | NOT NULL | bcrypt hashed password |
| `token_version` | UUID | NOT NULL | Rotating token invalidation key |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | Account creation timestamp |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW, ON UPDATE NOW | Last modification timestamp |

**Indexes**:
- Primary key on `id`
- Unique index on `username`
- Index on `token_version` (for JWT validation queries)

**Model Definition** (`src/models/user.py`):
```python
from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import uuid4, UUID

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    token_version: UUID = Field(default_factory=uuid4, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        nullable=False
    )
```

**Sample Data**:
```sql
INSERT INTO users (id, username, hashed_password, token_version, created_at, updated_at)
VALUES (
    '123e4567-e89b-12d3-a456-426614174000',
    'johndoe',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyW3wz.cYkTy',
    '987fcdeb-51a2-43f7-b890-123456789abc',
    '2025-10-10 12:00:00',
    '2025-10-10 12:00:00'
);
```

---

### Employee Table (Future)

**Table Name**: `employees`

**Purpose**: Extended profile information for users (future feature).

**Schema**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique employee identifier |
| `user_id` | UUID | FOREIGN KEY → users(id), UNIQUE | Associated user account |
| `first_name` | VARCHAR(255) | NOT NULL | Employee's first name |
| `last_name` | VARCHAR(255) | NOT NULL | Employee's last name |
| `email` | VARCHAR(255) | UNIQUE | Work email address |
| `department` | VARCHAR(100) | NULL | Department name |
| `position` | VARCHAR(100) | NULL | Job title/position |
| `hire_date` | DATE | NULL | Date of hire |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | Record creation |
| `updated_at` | DATETIME | NOT NULL, ON UPDATE NOW | Last update |

**Relationships**:
- One-to-one with `User` via `user_id`

---

## Field Details

### UUID Fields

**Purpose**: Unique identifiers that are globally unique and non-sequential.

**Format**: `123e4567-e89b-12d3-a456-426614174000` (UUID v4)

**Benefits**:
- No sequential ID exposure
- Safe for distributed systems
- Impossible to enumerate users

**Generation**:
```python
from uuid import uuid4

user_id = uuid4()  # Generates new UUID
```

### Password Hashing

**Algorithm**: bcrypt with cost factor 12

**Format**: `$2b$12$<salt><hash>` (60 characters)

**Example**:
```
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyW3wz.cYkTy
```

**Breakdown**:
- `$2b$` - bcrypt version identifier
- `12` - Cost factor (2^12 iterations)
- Next 22 chars - Salt
- Remaining chars - Hash

**Security**:
- Each password has unique salt
- Cost factor adjustable for future-proofing
- Slow by design (resistant to brute force)

### Token Version

**Purpose**: Enable stateless token invalidation.

**Type**: UUID v4

**Behavior**:
- Generated on user creation
- Rotated on:
  - Logout all devices (`POST /auth/logout-all`)
  - Password change (`POST /auth/change-password`)
- Embedded in JWT tokens
- Validated on every protected request

**Flow**:
```python
# Token creation
token_claims = {
    "sub": user.id,
    "token_version": user.token_version,  # ← Embedded
    ...
}

# Token validation
if token_claims["token_version"] != user.token_version:
    raise TokenInvalidatedError()  # Version mismatch
```

### Timestamps

**Fields**: `created_at`, `updated_at`

**Type**: `DATETIME` (stored in UTC)

**Behavior**:
- `created_at`: Set once on record creation
- `updated_at`: Automatically updated on record modification

**SQLModel Implementation**:
```python
from datetime import datetime

created_at: datetime = Field(default_factory=datetime.utcnow)
updated_at: datetime = Field(
    default_factory=datetime.utcnow,
    sa_column_kwargs={"onupdate": datetime.utcnow}
)
```

**⚠️ Note**: `onupdate` may not work as expected in all databases. Consider handling in application logic if issues arise.

---

## Queries

### Common Queries

#### Get User by Username
```sql
SELECT * FROM users WHERE username = 'johndoe';
```

#### Get User by ID
```sql
SELECT * FROM users WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

#### Validate Token Version
```sql
SELECT id, token_version FROM users 
WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

#### Check Username Availability
```sql
SELECT EXISTS(SELECT 1 FROM users WHERE username = 'johndoe');
```

#### Rotate Token Version
```sql
UPDATE users 
SET token_version = '987fcdeb-51a2-43f7-b890-123456789abc',
    updated_at = CURRENT_TIMESTAMP
WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

---

## Repository Layer

### UserRepository

**File**: `src/repositories/user.py`

**Methods**:

```python
class UserRepository:
    def add(self, user: User, session: Session) -> None:
        """Add user to session (does not commit)."""
        session.add(user)
    
    def get_by_id(self, user_id: UUID, session: Session) -> User | None:
        """Fetch user by ID."""
        return session.get(User, user_id)
    
    def get_by_username(self, username: str, session: Session) -> User | None:
        """Fetch user by username."""
        statement = select(User).where(User.username == username)
        return session.exec(statement).first()
    
    def get_all(self, session: Session, limit: int = 100) -> list[User]:
        """Fetch all users (with limit)."""
        statement = select(User).limit(limit)
        return list(session.exec(statement))
    
    def update(self, user: User, session: Session) -> None:
        """Update user (does not commit)."""
        session.add(user)  # Merge changes
```

**Design Notes**:
- Repositories **do not commit** transactions
- Service layer controls transaction boundaries
- Repositories return entities or `None`
- Use type hints for clarity

---

## Database Initialization

### Development (SQLite)

**Automatic Setup**:

```python
# src/main.py
from src.config.database import engine
from src.models.user import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    User.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)
```

**Database File**: `./dev.db` (created in project root)

**Inspection**:
```bash
# Using sqlite3
sqlite3 dev.db

# View schema
.schema users

# Query data
SELECT * FROM users;
```

### Production (PostgreSQL)

**Connection String**:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

**Migration Strategy** (future):
1. Install Alembic: `uv add alembic`
2. Initialize: `alembic init migrations`
3. Generate migrations: `alembic revision --autogenerate -m "message"`
4. Apply: `alembic upgrade head`

---

## Performance Considerations

### Indexes

**Current Indexes**:
- Primary key on `users.id` (automatic)
- Unique index on `users.username` (explicit)

**Future Optimization**:
- Index on `users.token_version` if query performance degrades
- Composite index on frequently combined filters

### Query Optimization

**Best Practices**:
```python
# ✅ Good: Fetch specific columns
statement = select(User.id, User.username).where(...)

# ❌ Avoid: Unnecessary SELECT *
statement = select(User).where(...)  # Fetches all columns
```

**Pagination**:
```python
# Add limit/offset for large result sets
statement = select(User).limit(100).offset(0)
```

### Connection Pooling

**SQLite** (development):
- Single-threaded, no pooling needed

**PostgreSQL** (production):
```python
from sqlmodel import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Max connections
    max_overflow=10,     # Extra connections if pool full
    pool_pre_ping=True,  # Verify connections before use
)
```

---

## Data Integrity

### Constraints

**Enforced**:
- ✅ Primary key uniqueness
- ✅ Username uniqueness
- ✅ NOT NULL constraints

**Not Enforced** (application-level):
- Password complexity (≥8 chars)
- Username format (≥4 chars, no spaces)

### Transactions

**ACID Properties**:
- **Atomic**: All-or-nothing operations
- **Consistent**: Database remains in valid state
- **Isolated**: Concurrent transactions don't interfere
- **Durable**: Committed data persists

**Service Layer Example**:
```python
def create_user(data: UserCreate, session: Session) -> User:
    try:
        # Check uniqueness
        if self.user_repo.get_by_username(data.username, session):
            raise UserAlreadyExistsError()
        
        # Create user
        user = User(...)
        self.user_repo.add(user, session)
        
        # Commit (atomic)
        session.commit()
        session.refresh(user)
        
        return user
    except Exception:
        session.rollback()  # Rollback on error
        raise
```

---

## Backup & Recovery

### SQLite (Development)

**Backup**:
```bash
# Simple file copy
cp dev.db dev.db.backup

# Using sqlite3
sqlite3 dev.db ".backup 'backup.db'"
```

**Restore**:
```bash
cp dev.db.backup dev.db
```

### PostgreSQL (Production)

**Backup**:
```bash
# Full database dump
pg_dump -U user -d dbname > backup.sql

# Compressed backup
pg_dump -U user -d dbname | gzip > backup.sql.gz
```

**Restore**:
```bash
psql -U user -d dbname < backup.sql
```

**Automated Backups** (future):
- Daily automated backups
- Off-site storage (S3, etc.)
- Retention policy (keep 30 days)

---

## Migration Strategy (Future)

### Alembic Setup

```bash
# Install
uv add alembic

# Initialize
alembic init migrations

# Configure (migrations/env.py)
from src.models.user import User
target_metadata = User.metadata
```

### Creating Migrations

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add email to users"

# Review generated migration
# Edit if needed

# Apply migration
alembic upgrade head
```

### Migration File Example

```python
# migrations/versions/001_add_email.py
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade():
    op.drop_index('ix_users_email', 'users')
    op.drop_column('users', 'email')
```

---

## Database Maintenance

### Monitoring

**Metrics to Track**:
- Query execution time
- Connection pool usage
- Database size growth
- Index usage statistics

### Optimization

**Regular Tasks**:
- Analyze query performance (EXPLAIN)
- Update statistics (ANALYZE)
- Rebuild indexes if fragmented
- Archive old data

**SQLite Maintenance**:
```bash
# Optimize database
sqlite3 dev.db "VACUUM;"

# Analyze statistics
sqlite3 dev.db "ANALYZE;"
```

---

## Security Considerations

### Sensitive Data

**Encrypted Fields**:
- `hashed_password` - bcrypt hashed, never stored plain

**Not Logged**:
- Passwords (plain or hashed)
- Full `token_version` (log only truncated)

### SQL Injection Prevention

**✅ Use parameterized queries**:
```python
# Safe: Parameterized
statement = select(User).where(User.username == username)

# Unsafe: String concatenation
query = f"SELECT * FROM users WHERE username = '{username}'"  # ❌
```

SQLModel/SQLAlchemy automatically uses parameterized queries.

---

## References

- [Architecture Overview](architecture.md)
- [API Specification](api-spec.md)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---
*Last Updated: October 10, 2025*
