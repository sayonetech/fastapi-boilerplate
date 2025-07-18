# Madcrow Backend Documentation

Welcome to the Madcrow Backend documentation. This directory contains detailed documentation for various aspects of the application.

## ✨ Key Features

- **🔐 Secure Authentication** - JWT-based authentication with refresh tokens
- **🎯 Event-Driven Architecture** - Blinker-based event system for loose coupling
- **🛡️ Comprehensive Security** - Security headers, route protection, and audit logging
- **🏗️ Class-Based Views** - Clean, organized API endpoints with CBV pattern
- **💾 Redis Integration** - Caching, sessions, and token management
- **📊 Error Handling** - Structured error responses and logging
- **🚀 Production Ready** - Comprehensive production checklist and monitoring

## 📚 Documentation Index

### 🚀 Getting Started

- **[Getting Started](./getting-started.md)** - Complete setup guide for new developers
- **[API Reference](./api-reference.md)** - Quick reference for all API endpoints
- **[Commands](./commands.md)** - CLI commands for administration and management

### 🔐 Authentication & Security

- **[Authentication System](./authentication.md)** - Secure authentication with JWT tokens
- **[Protection System](./protection-system.md)** - Route protection and authorization middleware
- **[Security Headers](./security-headers.md)** - Security headers middleware implementation
- **[Login Decorator](./login-decorator.md)** - Login decorator usage and patterns

### 🏗️ Core Architecture

- **[Event System](./events.md)** - Event-driven architecture with Blinker signals
- **[Class-Based Views (CBV)](./class-based-views.md)** - FastAPI class-based views implementation guide
- **[Error Handling](./error-handling.md)** - Comprehensive error handling system

### 💾 Data & Infrastructure

- **[Database Setup](./database-setup.md)** - Database configuration and migration guide
- **[Redis Extension](./redis-extension.md)** - Redis integration for caching and sessions

### 📱 API Documentation

- **[Profile API](./profile-api.md)** - Profile API documentation and usage

### 🚀 Production & Deployment

- **[Production Checklist](./production-checklist.md)** - Comprehensive production readiness checklist

## 🚀 Quick Start

**New to Madcrow Backend?** Start with the [Getting Started Guide](./getting-started.md) for a complete setup walkthrough.

### 🔍 Quick Navigation

| I want to...             | Go to                                             |
| ------------------------ | ------------------------------------------------- |
| Set up the project       | [Getting Started Guide](./getting-started.md)     |
| Implement authentication | [Authentication System](./authentication.md)      |
| Create event handlers    | [Event System](./events.md)                       |
| Build new API endpoints  | [Class-Based Views](./class-based-views.md)       |
| Configure security       | [Security Headers](./security-headers.md)         |
| Set up database          | [Database Setup](./database-setup.md)             |
| Deploy to production     | [Production Checklist](./production-checklist.md) |

### Step-by-Step Setup

1. **Getting Started**: Follow the [Getting Started Guide](./getting-started.md) for complete setup
2. **Authentication**: Set up user authentication with the [Authentication System guide](./authentication.md)
3. **Database Setup**: Use the [Database Setup guide](./database-setup.md) for database configuration
4. **Event System**: Learn about event-driven architecture with the [Event System guide](./events.md)
5. **Development**: Check the [CBV guide](./class-based-views.md) for implementing new API endpoints
6. **Security Setup**: Follow the [Security Headers guide](./security-headers.md) to configure security middleware
7. **Protection System**: Configure route protection with the [Protection System guide](./protection-system.md)
8. **Production Readiness**: Review the [Production Checklist](./production-checklist.md) before deployment

## 🔍 Production Audit

Run the production readiness audit to check your configuration:

```bash
# Run production audit script
uv run python scripts/production_audit.py

# Test security headers
uv run python test_security_headers.py
```

## 📖 Main Documentation

For general setup and usage instructions, see the main [README.md](../README.md) in the project root.

## 🔗 External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

## 📝 Contributing

When adding new documentation:

1. Create markdown files in this `docs/` directory
2. Update this index with links to new documentation
3. Follow the existing documentation style and structure
4. Include practical examples and code snippets
