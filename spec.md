# Backend Application Specification

## Overview

This document outlines the architecture and implementation requirements for transforming our FastAPI **PUT /users/password**
- Change current user's password
- Headers: `Authorization: Bearer <token>`
- Input: `{ "current_password": "string", "new_password": "string" }`
- Output: `{ "message": "Password changed successfully" }`
- Note: Generates new validation key, invalidating all existing tokenstype into a production-ready backend application. The system provides user management capabilities with JWT-based authentication.

## Technology Stack

### Core Technologies
- **Framework**: FastAPI (Python 3.13+)
- **ORM**: SQLModel (for database management)
# Minimal API Specification

### Endpoints

Auth:
| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | /auth/register | Register + token pair |
| POST | /auth/login | Credentials → token pair |
| POST | /auth/refresh | New access token (refresh required) |
| POST | /auth/logout-all | Invalidate all user tokens |
| POST | /auth/change-password | Change password & rotate token_key |

Users:
| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | /users | Create user |
| GET | /users | List users (auth) |

### JWT Claims
`sub`, `key`, `kind` (`access|refresh`), `iat`, `exp`.
`key` rotates on logout-all & password change (invalidates prior tokens).

### Validation
Username ≥4 chars, no spaces. Password ≥8 chars.

### Errors
| HTTP | When |
| ---- | ---- |
| 401 | Invalid credentials / token invalid / key mismatch |
| 404 | User not found |
| 409 | Username exists |
| 422 | Validation failure |
| 400 | Other domain error |

Body: `{ "detail": "Message" }`

### Scope (Omitted Intentionally)
Migrations, tests, rate limiting, OAuth, health endpoints.

### Notes
SQLite used for dev; schema auto-created at startup; no data migrations.