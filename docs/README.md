# Backend Documentation

Welcome to the fs-backend documentation. This directory contains comprehensive guides and references for the entire system.

## 📚 Documentation Index

### Getting Started
- **[Setup Guide](setup.md)** - Installation, environment configuration, and development server setup using uv
- **[Architecture Overview](architecture.md)** - System design, layered architecture, and design patterns

### API Documentation
- **[API Specification](api-spec.md)** - Complete endpoint reference with all endpoints, parameters, and examples
- **[Authentication](authentication.md)** - JWT authentication flows, token mechanism, and security details
- **[Error Handling](errors.md)** - Error codes, response formats, and troubleshooting

### Development & Operations
- **[Configuration](configuration.md)** - Environment variables, settings, and deployment configuration
- **[Database Schema](database.md)** - Data models, relationships, and query patterns
- **[Development Guide](development.md)** - Contributing guidelines, code style, and workflows

## 🚀 Quick Navigation

### For New Developers
1. Start with [Setup Guide](setup.md) to install and run locally
2. Review [Architecture Overview](architecture.md) to understand the codebase structure
3. Explore [API Specification](api-spec.md) via Swagger UI at http://127.0.0.1:3001/docs

### For API Users
1. Check [API Specification](api-spec.md) for endpoint documentation
2. Review [Authentication](authentication.md) for JWT flows
3. See [Error Handling](errors.md) for error responses

### For Operations/DevOps
1. Review [Configuration](configuration.md) for environment setup
2. Check [Database Schema](database.md) for data structure
3. Follow [Setup Guide](setup.md) for deployment

## 📖 Documentation Structure

Each document is self-contained but linked to others:

```
Setup Guide
    ↓
Architecture → API Spec ← Authentication
    ↓              ↓              ↓
Database     Error Handling   Development
    ↓              ↓              ↓
Configuration ←← All Topics ←→ Development Guide
```

## 🔗 External References

### Project Resources
- **Main README**: [../README.md](../README.md) - Project overview and quick start
- **Source Code**: [../app](../app) - Application code
- **Tests**: [../tests](../tests) - Test suite
- **Configuration**: [../pyproject.toml](../pyproject.toml) - Project metadata

### Technology Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [bcrypt Documentation](https://github.com/pyca/bcrypt)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

## 🎯 Key Topics

### Authentication & Security
- JWT token mechanism with rotating keys
- Password hashing with bcrypt
- Token invalidation without Redis
- Role-based access control (RBAC)
- See: [Authentication](authentication.md)

### API Design
- RESTful endpoints
- Standardized error responses
- Pagination support
- Authorization checks
- See: [API Specification](api-spec.md)

### Database
- SQLModel ORM
- Employee hierarchy (self-join)
- Time and absence entry tracking
- Indexing strategy
- See: [Database Schema](database.md)

### Architecture
- Layered architecture (API → Service → Repository → Domain)
- Dependency injection
- Domain-driven exceptions
- Transaction management
- See: [Architecture Overview](architecture.md)

## 💡 Common Tasks

### "How do I start the server?"
See [Setup Guide - Running the Application](setup.md#running-the-application)

### "How do I authenticate?"
See [Authentication - Overview](authentication.md#overview) and [API - Authentication Endpoints](api-spec.md#authentication-endpoints)

### "How do I manage employees and hierarchy?"
See [API - Employee Management Endpoints](api-spec.md#employee-management-endpoints) and [Architecture - Employee Hierarchy](architecture.md#employee-hierarchy)

### "How do I track time entries?"
See [API - Time Entry Endpoints](api-spec.md#time-entry-endpoints)

### "What environment variables are needed?"
See [Configuration](configuration.md) and [Setup Guide - Environment Variables](setup.md#environment-variables-reference)

### "How do I run tests?"
See [Development Guide](development.md) - Testing section

### "How is the codebase organized?"
See [Architecture Overview - Project Structure](architecture.md#project-structure)

### "What are authorization rules?"
See [Authentication - Authorization](authentication.md#authorization-role-based-access-control)

## ✅ Documentation Quality

- ✅ Updated for current codebase (November 7, 2025)
- ✅ Includes all implemented features
- ✅ Code examples tested and working
- ✅ Clear navigation and cross-references
- ✅ Security best practices documented
- ✅ Troubleshooting guides included

## 📝 Contributing to Documentation

When updating documentation:

1. **Keep it accurate**: Update examples to match current code
2. **Use clear language**: Assume technical but not domain-expert audience
3. **Include examples**: Provide working code snippets
4. **Cross-reference**: Link to related sections
5. **Update index**: Add new documents to this README
6. **Version date**: Update "Last Updated" footer in each document

## 🔄 Document Maintenance

| Document | Last Updated | Status |
|----------|--------------|--------|
| [README.md](README.md) | Nov 7, 2025 | ✅ Current |
| [Setup Guide](setup.md) | Nov 7, 2025 | ✅ Current |
| [Architecture](architecture.md) | Nov 7, 2025 | ✅ Current |
| [Authentication](authentication.md) | Nov 7, 2025 | ✅ Current |
| [API Specification](api-spec.md) | Nov 7, 2025 | ✅ Current |
| [Database Schema](database.md) | Nov 7, 2025 | ✅ Current |
| [Configuration](configuration.md) | Oct 10, 2025 | ⚠️ Review needed |
| [Error Handling](errors.md) | Oct 10, 2025 | ⚠️ Review needed |
| [Development](development.md) | Oct 10, 2025 | ⚠️ Review needed |

## 🆘 Getting Help

1. **Check the docs**: Search this documentation first
2. **Review examples**: See [API Specification](api-spec.md#complete-example-user-registration-flow)
3. **Check the code**: Look at test files in [../tests](../tests)
4. **Ask questions**: Create an issue or discussion on the repository

---

**Last Updated**: November 7, 2025  
**Documentation Version**: 1.0.0  
**Project Version**: 0.1.0
