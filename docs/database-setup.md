# Database Setup

Complete guide for setting up and configuring the PostgreSQL database for Madcrow Backend.

## Overview

This guide covers database configuration, connection setup, migrations, and troubleshooting for the Madcrow Backend application using PostgreSQL with Alembic migrations.

## Prerequisites

- PostgreSQL 15+ installed locally or via Docker
- Python 3.12+ with uv package manager
- Docker and Docker Compose (recommended)

## Quick Start

### 1. Start Database with Docker (Recommended)

```bash
# Start PostgreSQL database
docker compose -p madcrow up -d db

# Verify database is running
docker ps | grep postgres
```

### 2. Configure Environment

Copy and configure your environment file:

```bash
# Copy environment template
cp .env.example .env

# Edit database configuration in .env
DB_USERNAME=postgres
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=madcrow
```

### 3. Run Database Migrations

```bash
# Run Alembic migrations
uv run alembic upgrade head

# Verify migration status
uv run alembic current
```

## Detailed Configuration

### Database Connection Settings

Configure these environment variables in your `.env` file:

```bash
# Database Connection
DB_USERNAME=postgres          # Database username
DB_PASSWORD=123456           # Database password
DB_HOST=localhost            # Database host
DB_PORT=5432                # Database port
DB_DATABASE=madcrow         # Database name

# Connection Pool Settings
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_MAX_OVERFLOW=10
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_POOL_PRE_PING=false

# Development Settings
DB_CONNECTION_TEST_ON_STARTUP=true   # Test connection on startup
SQLALCHEMY_ECHO=false               # Enable SQL query logging
```

### Migration Management

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Check migration history
uv run alembic history --verbose

# Rollback to previous migration
uv run alembic downgrade -1
```

## Troubleshooting

### Connection Issues

**Problem**: Application fails to connect to database

**Solutions**:

1. **Skip connection test for development**:

   ```bash
   # Add to .env file
   DB_CONNECTION_TEST_ON_STARTUP=false
   ```

2. **Verify database is running**:

   ```bash
   # Check PostgreSQL port
   lsof -i :5432

   # Check Docker containers
   docker ps | grep postgres

   # Start database if not running
   docker compose -p madcrow up -d db
   ```

3. **Test connection manually**:

   ```bash
   # Using psql
   psql -h localhost -p 5432 -U postgres -d madcrow

   # Using Docker
   docker exec -it madcrow-db-1 psql -U postgres -d madcrow
   ```

### Migration Issues

**Problem**: Alembic migration failures

**Solutions**:

1. **Check current migration status**:

   ```bash
   uv run alembic current
   uv run alembic history
   ```

2. **Reset migrations** (development only):
   ```bash
   # Drop and recreate database
   docker compose -p madcrow down -v
   docker compose -p madcrow up -d db
   uv run alembic upgrade head
   ```

### Performance Issues

**Problem**: Slow database queries

**Solutions**:

1. **Enable query logging**:

   ```bash
   SQLALCHEMY_ECHO=true
   ```

2. **Adjust connection pool**:
   ```bash
   SQLALCHEMY_POOL_SIZE=10
   SQLALCHEMY_MAX_OVERFLOW=5
   ```

## Environment-Specific Configuration

### Development Environment

```bash
# Development settings in .env
DB_CONNECTION_TEST_ON_STARTUP=false  # Skip connection test for faster startup
SQLALCHEMY_ECHO=true                 # Enable SQL query logging
SQLALCHEMY_POOL_SIZE=5               # Smaller pool for development
```

### Production Environment

```bash
# Production settings
DB_CONNECTION_TEST_ON_STARTUP=true   # Test connection on startup
SQLALCHEMY_ECHO=false                # Disable SQL logging for performance
SQLALCHEMY_POOL_SIZE=30              # Larger pool for production
SQLALCHEMY_POOL_PRE_PING=true        # Enable connection health checks
```

## Examples

### Basic Database Operations

```python
from sqlmodel import Session, select
from src.entities.account import Account
from src.extensions.ext_db import db_engine

# Get database session
with Session(db_engine.get_engine()) as session:
    # Query users
    users = session.exec(select(Account)).all()

    # Create new user
    new_user = Account(name="John Doe", email="john@example.com")
    session.add(new_user)
    session.commit()
```

### Health Check Usage

```bash
# Check database health
curl http://localhost:5001/v1/health/

# Test database connection
curl http://localhost:5001/v1/health/ready
```

## Related Documentation

- **[Getting Started](./getting-started.md)** - Complete setup guide
- **[Authentication](./authentication.md)** - User authentication system
- **[Production Checklist](./production-checklist.md)** - Production deployment guide
- **[Error Handling](./error-handling.md)** - Database error handling patterns
