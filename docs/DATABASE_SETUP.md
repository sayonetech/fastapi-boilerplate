# Database Setup Guide

## Quick Fix for Current Error

The application is failing to connect to the database during startup. Here are the solutions:

### Option 1: Disable Connection Test (Recommended for Development)

Add this to your `.env` file:

```bash
DB_CONNECTION_TEST_ON_STARTUP=false
```

This will allow the application to start even if the database is not available.

### Option 2: Start the Database

If you want to use the database, make sure it's running:

```bash
# Start the database using Docker Compose
docker compose -p madcrow up -d db

# Or start all services
docker compose -p madcrow up -d
```

## Database Configuration

Your current database configuration (from `.env.example`):

```bash
DB_USERNAME=postgres
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=madcrow
```

## Troubleshooting Steps

### 1. Check if Database is Running

```bash
# Check if PostgreSQL is running on port 5432
lsof -i :5432

# Or check Docker containers
docker ps | grep postgres
```

### 2. Test Database Connection Manually

```bash
# Using psql (if installed)
psql -h localhost -p 5432 -U postgres -d madcrow

# Using Docker
docker exec -it madcrow-db-1 psql -U postgres -d madcrow
```

### 3. Check Database Logs

```bash
# Check Docker container logs
docker logs madcrow-db-1

# Or follow logs in real-time
docker logs -f madcrow-db-1
```

### 4. Create Database if Missing

```sql
-- Connect as postgres user and create database
CREATE DATABASE madcrow;
```

## Environment-Specific Settings

### Development

```bash
DB_CONNECTION_TEST_ON_STARTUP=false  # Skip connection test
SQLALCHEMY_ECHO=true                 # Enable SQL logging
```

### Production

```bash
DB_CONNECTION_TEST_ON_STARTUP=true   # Test connection on startup
SQLALCHEMY_ECHO=false                # Disable SQL logging
```

## Health Check Endpoints

Once the application starts, you can check database health:

- `GET /v1/health/` - General health (includes database check)
- `GET /v1/health/ready` - Readiness probe (includes database check)
- `GET /v1/database/test` - Direct database connection test

## Database Migration

If you need to run database migrations:

```bash
# Run Alembic migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "Description"
```
