# Database Schema

Complete database schema documentation for fs-backend.

## Overview

**Database ORM**: SQLModel (Pydantic + SQLAlchemy)  
**Schema Management**: Auto-created on startup from SQLModel models  
**Supported Databases**: 
- SQLite (default for development)
- PostgreSQL (recommended for production)

---

## Entity Relationship Diagram

```
┌────────────────┐         ┌──────────────────┐
│     users      │         │    employees     │
├────────────────┤         ├──────────────────┤
│ id (PK, UUID)  │◄────────┤ user_id (FK)     │
│ username       │         │ first_name       │
│ password_hash  │         │ last_name        │
│ token_key      │         │ birthday         │
│ is_superuser   │         │ hour_model       │
│ created_at     │         │ pause_time_min   │
│ updated_at     │         │ start_from       │
└────────────────┘         │ supervisor_id(FK)│
         │                 └──────────────────┘
         │                          │
         │                          │ self-reference
         │                          │ (hierarchy)
         │                          │
    ┌────┴────────┐                └─┬──┐
    │             │                  │  │
┌───▼────────────┐  ┌───────────────▼┐ │
│  time_entries  │  │ employee_hier..│ │
├───────────────┐│  └─────────────────┘ │
│ id (PK)       ││                      │
│ user_id (FK)  ││  ┌──────────────────┐│
│ entry_type    ││  │absence_entries   ││
│ date_time     ││  ├──────────────────┤│
│ created_by(FK)││  │ id (PK)          ││
│ created_at    ││  │ user_id (FK)     ││
└────────────────┤  │ entry_type       ││
                 │  │ date_begin       ││
                 │  │ date_end         ││
                 │  │ created_by (FK)  ││
                 │  │ created_at       ││
                 │  └──────────────────┘│
                 │                      │
                 └──────────────────────┘
```

---

## Tables

### users

**Purpose**: Authentication principal and user account storage

**Table Name**: `users`

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | UUID | PRIMARY KEY | Unique user identifier |
| `username` | VARCHAR | UNIQUE, NOT NULL, INDEX | Login identifier (≥4 chars, no spaces) |
| `password_hash` | VARCHAR | NOT NULL | Bcrypt hashed password (60 chars) |
| `token_key` | UUID | NOT NULL, INDEX | Current token version for invalidation |
| `is_superuser` | BOOLEAN | NOT NULL, DEFAULT FALSE | Admin role flag |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes**:
```sql
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_token_key ON users(token_key);
```

**Model Definition** (`app/models/user.py`):
```python
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    token_key: uuid.UUID = Field(default_factory=uuid.uuid4, index=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    employee: Optional["Employee"] = Relationship(back_populates="user", cascade_delete=True)
```

**Sample Data**:
```sql
INSERT INTO users (id, username, password_hash, token_key, is_superuser) VALUES
  ('550e8400-e29b-41d4-a716-446655440000', 'john.doe', '$2b$12$...', 'abc12345...', FALSE),
  ('550e8400-e29b-41d4-a716-446655440099', 'admin.user', '$2b$12$...', 'xyz98765...', TRUE);
```

---

### employees

**Purpose**: Employee profile with work configuration and hierarchy

**Table Name**: `employees`

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `user_id` | UUID | PRIMARY KEY, FOREIGN KEY → users.id | Link to user account |
| `first_name` | VARCHAR | NOT NULL | Employee first name |
| `last_name` | VARCHAR | NOT NULL | Employee last name |
| `supervisor_id` | UUID | FOREIGN KEY → employees.user_id, INDEX, NULLABLE | Manager/supervisor (self-join hierarchy) |
| `birthday` | DATE | NOT NULL | Date of birth |
| `hour_model` | ENUM | NOT NULL | Work hours model (e30=30h, e35=35h, e40=40h) |
| `pause_time_minutes` | INTEGER | NOT NULL | Daily break duration in minutes |
| `start_from` | DATE | NOT NULL | Contract/employment start date |

**Enums**:
```python
class HourModel(Enum):
    e30 = 6   # 30 hours/week
    e35 = 7   # 35 hours/week
    e40 = 8   # 40 hours/week
```

**Model Definition** (`app/models/employee.py`):
```python
class Employee(SQLModel, table=True):
    __tablename__ = "employees"
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="users.id")
    first_name: str
    last_name: str
    supervisor_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="employees.user_id", index=True
    )
    birthday: date
    hour_model: HourModel
    pause_time_minutes: int
    start_from: date

    user: "User" = Relationship(back_populates="employee")
    supervisor: Optional["Employee"] = Relationship(
        back_populates="subordinates",
        sa_relationship_kwargs={"remote_side": "Employee.user_id"},
    )
    subordinates: list["Employee"] = Relationship(back_populates="supervisor")
```

**Relationships**:
- Many-to-One: `Employee.supervisor_id` → `Employee.user_id` (self-join for hierarchy)
- One-to-Many: `Employee.subordinates` ← reverse relationship
- One-to-One: `Employee.user` → `User`

**Sample Data**:
```sql
INSERT INTO employees (user_id, first_name, last_name, supervisor_id, birthday, hour_model, pause_time_minutes, start_from) VALUES
  ('550e8400-e29b-41d4-a716-446655440000', 'John', 'Doe', NULL, '1990-05-15', 8, 30, '2024-01-15'),
  ('550e8400-e29b-41d4-a716-446655440001', 'Jane', 'Smith', '550e8400-e29b-41d4-a716-446655440000', '1992-03-22', 8, 30, '2024-02-01');
```

---

### time_entries

**Purpose**: Track arrival and departure times for employees

**Table Name**: `time_entries`

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique entry identifier |
| `user_id` | UUID | FOREIGN KEY → employees.user_id, INDEX | Which employee |
| `entry_type` | ENUM | NOT NULL | "arrival" or "departure" |
| `date_time` | DATETIME | NOT NULL, INDEX | When the entry was recorded |
| `created_by` | UUID | FOREIGN KEY → users.id, INDEX | Who created the entry |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW(), INDEX | Timestamp of creation |

**Enums**:
```python
class TimeEntryType(Enum):
    Arrival = "arrival"
    Departure = "departure"
```

**Model Definition** (`app/models/time_entry.py`):
```python
class TimeEntry(SQLModel, table=True):
    __tablename__ = "time_entries"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="employees.user_id", index=True)
    entry_type: TimeEntryType
    date_time: datetime = Field(index=True)
    created_by: uuid.UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    employee: "Employee" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "TimeEntry.user_id"}
    )
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "TimeEntry.created_by"}
    )
```

**Sample Data**:
```sql
INSERT INTO time_entries (user_id, entry_type, date_time, created_by, created_at) VALUES
  ('550e8400-e29b-41d4-a716-446655440000', 'arrival', '2025-11-07 08:30:00', '550e8400-e29b-41d4-a716-446655440000', NOW()),
  ('550e8400-e29b-41d4-a716-446655440000', 'departure', '2025-11-07 17:30:00', '550e8400-e29b-41d4-a716-446655440000', NOW());
```

---

### absence_entries

**Purpose**: Track absence periods (sickness, vacation, etc.)

**Table Name**: `absence_entries`

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique entry identifier |
| `user_id` | UUID | FOREIGN KEY → employees.user_id, INDEX | Which employee |
| `entry_type` | ENUM | NOT NULL | Type of absence (sickness, vacation, other) |
| `date_begin` | DATE | NOT NULL, INDEX | Start date of absence |
| `date_end` | DATE | NOT NULL, INDEX | End date of absence (inclusive) |
| `created_by` | UUID | FOREIGN KEY → users.id, INDEX | Who created the entry |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW(), INDEX | Timestamp of creation |

**Enums**:
```python
class AbsenceEntryType(Enum):
    Sickness = "sickness"
    Vacation = "vacation"
    Other = "other"
```

**Model Definition** (`app/models/absence_entry.py`):
```python
class AbsenceEntry(SQLModel, table=True):
    __tablename__ = "absence_entries"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="employees.user_id", index=True)
    entry_type: AbsenceEntryType
    date_begin: date = Field(index=True)
    date_end: date = Field(index=True)
    created_by: uuid.UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    employee: "Employee" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "AbsenceEntry.user_id"}
    )
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "AbsenceEntry.created_by"}
    )
```

**Sample Data**:
```sql
INSERT INTO absence_entries (user_id, entry_type, date_begin, date_end, created_by, created_at) VALUES
  ('550e8400-e29b-41d4-a716-446655440000', 'vacation', '2025-11-10', '2025-11-14', '550e8400-e29b-41d4-a716-446655440099', NOW()),
  ('550e8400-e29b-41d4-a716-446655440000', 'sickness', '2025-11-03', '2025-11-03', '550e8400-e29b-41d4-a716-446655440000', NOW());
```

---

### employee_hierarchy *(optional, for caching)*

**Purpose**: Cache employee supervisor chains for performance optimization

**Table Name**: `employee_hierarchy`

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `employee_id` | UUID | FOREIGN KEY → employees.user_id, PRIMARY KEY (part 1) | Employee in hierarchy |
| `supervisor_id` | UUID | FOREIGN KEY → employees.user_id, PRIMARY KEY (part 2) | Supervisor in chain |
| `distance` | INTEGER | NOT NULL | Hierarchical distance (1=direct supervisor, 2=super's supervisor) |

**Purpose**: Materialized view of hierarchy chains for fast "is_supervisor_of" queries

**Note**: This table is derived data; can be rebuilt if corrupted using stored procedures or application logic.

---

## Field Details

### UUID Fields

**Purpose**: Globally unique, non-sequential identifiers

**Format**: RFC 4122 UUID v4  
**Example**: `550e8400-e29b-41d4-a716-446655440000`

**Benefits**:
- ✅ Globally unique across systems
- ✅ No sequential ID exposure (security)
- ✅ Safe for distributed systems
- ✅ Impossible to enumerate

**Generation**:
```python
from uuid import uuid4
user_id = uuid4()  # New UUID
```

### Password Hashing

**Algorithm**: bcrypt (adaptive hashing)

**Format**: `$2b$12$<salt><hash>` (60 characters)

**Example**: `$2b$12$R9h7cIPz0gi.URNNF3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUe`

**Breakdown**:
- `$2b$` - bcrypt version
- `12` - Cost factor (2^12 = 4096 iterations)
- Next 22 chars - Random salt
- Remaining - Salted hash

**Features**:
- ✅ Unique salt per password
- ✅ Slow by design (resistant to brute force)
- ✅ Cost adjustable for future hardware changes
- ✅ Standard bcrypt format

### Token Key

**Purpose**: Enable stateless token invalidation without Redis

**Type**: UUID v4  
**Storage**: User.token_key column

**Mechanism**:
```python
# On token creation
token_payload = {
    "sub": user.id,
    "key": user.token_key,  # ← Embed current version
    "exp": ...,
}

# On token validation
if token.key != user.token_key:  # Version mismatch
    raise TokenRevokedError()  # Token invalidated
```

**Rotation** (logout or password change):
```python
user.token_key = uuid.uuid4()  # New version
session.commit()  # All old tokens now invalid
```

### Timestamps

**Format**: ISO 8601 with timezone (UTC)  
**Example**: `2025-11-07T10:30:00Z`

**Fields**:
- `created_at`: Set once on record creation
- `updated_at`: Updated on record modification

**Implementation**:
```python
from datetime import datetime, timezone

created_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc)
)
updated_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
)
```

**Time Zone**: All timestamps stored in UTC. Frontend handles local conversion.

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
