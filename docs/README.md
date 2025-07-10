# Madcrow Backend Documentation

Welcome to the Madcrow Backend documentation. This directory contains detailed documentation for various aspects of the application.

## 📚 Documentation Index

### 🚀 Production & Deployment
- **[Production Checklist](./PRODUCTION_CHECKLIST.md)** - Comprehensive production readiness checklist
- **[Security Headers](./SECURITY_HEADERS.md)** - Security headers middleware implementation

### 🏗️ Architecture & Development
- **[Class-Based Views (CBV)](./CBV_README.md)** - FastAPI class-based views implementation guide
- **[Database Setup](./DATABASE_SETUP.md)** - Database configuration and migration guide

## 🚀 Quick Start

1. **Production Readiness**: Review the [Production Checklist](./PRODUCTION_CHECKLIST.md) before deployment
2. **Security Setup**: Follow the [Security Headers guide](./SECURITY_HEADERS.md) to configure security middleware
3. **Database Setup**: Use the [Database Setup guide](./DATABASE_SETUP.md) for database configuration
4. **Development**: Check the [CBV guide](./CBV_README.md) for implementing new API endpoints

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
