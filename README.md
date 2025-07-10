# Beco Madcrow

[![Quality Gate Status](https://sonarqube.sayone.team/api/project_badges/measure?project=madcrow-backend&metric=alert_status&token=sqb_28e49476b790a9450fd7cdec5cddda4f8727d262)](https://sonarqube.sayone.team/dashboard?id=madcrow-backend)

## Usage

1. Start the docker-compose stack

   The backend require Redis which can be started together using `docker-compose`.

   ```bash
   docker compose -p madcrow up -d
   ```

2. Copy `.env.example` to `.env`

   ```bash
   cp .env.example .env
   ```

3. Generate a `SECRET_KEY` in the `.env` file.

   bash for Linux
   ```bash
   sed -i "/^SECRET_KEY=/c\SECRET_KEY=$(openssl rand -base64 42)" .env
   ```
   bash for Mac
   ```bash
   secret_key=$(openssl rand -base64 42)
   sed -i '' "/^SECRET_KEY=/c\\
   SECRET_KEY=${secret_key}" .env
   ```

4. Create environment.

   We service uses [UV](https://docs.astral.sh/uv/) to manage dependencies.
   First, you need to add the uv package manager, if you don't have it already.

   ```bash
   pip install uv
   # Or on macOS
   brew install uv
   ```

5. Install dependencies

   ```bash
   uv sync --dev
   ```

6. Set up the database

   ```bash
   # Apply database migrations
   uv run alembic upgrade head
   ```

7. Start backend

   ```bash
   uv run python main.py
   ```

## Database Setup and Migrations

### Prerequisites
1. Ensure PostgreSQL is running and accessible
2. Create a database named `madcrow` (or update `DB_DATABASE` in `.env`)
3. Update database credentials in `.env` file

### Database Migration Commands (Alembic)

The project uses Alembic for database migrations. The migration system is already configured to work with our application's database settings.

#### 1. Check Current Migration State
```bash
uv run alembic current
```
> *Shows the current migration revision applied to the database.*

#### 2. Apply All Migrations (First Time Setup)
```bash
uv run alembic upgrade head
```
> *This applies all migrations to bring your database schema up to date. Run this after setting up the database.*

#### 3. Create a New Migration After Changing Models
```bash
uv run alembic revision --autogenerate -m "describe your change"
```
> *Replace `"describe your change"` with a meaningful message like "add user table" or "add email index".*

#### 4. Apply New Migrations
```bash
uv run alembic upgrade head
```
> *Apply any new migrations to the database.*

#### 5. View Migration History
```bash
uv run alembic history
```
> *Shows all available migrations and their status.*

#### 6. Downgrade (Undo) the Last Migration
```bash
uv run alembic downgrade -1
```
> *You can also downgrade to a specific revision by replacing `-1` with the revision ID.*

#### 7. Reset Database (Development Only)
```bash
# WARNING: This will delete all data!
uv run alembic downgrade base  # Remove all migrations
uv run alembic upgrade head    # Reapply all migrations
```

### Migration Configuration Notes

- **Automatic Configuration**: Alembic is configured to use your `.env` file database settings
- **Model Detection**: Migrations automatically detect changes in `src/entities/` models
- **Database Driver**: Uses `postgresql+psycopg` driver for PostgreSQL
- **Import Fixes**: Migration files are automatically configured with required imports

### Troubleshooting Migrations

#### Issue: "ModuleNotFoundError" during migration
**Solution**: Ensure all dependencies are installed:
```bash
uv sync --dev
```

#### Issue: "sqlmodel not found" in migration file
**Solution**: The migration file needs the sqlmodel import. This is automatically added to new migrations.

#### Issue: Database connection errors
**Solution**: Check your `.env` file database settings:
```bash
# Verify database connection
uv run python -c "from src.configs import madcrow_config; print(madcrow_config.sqlalchemy_database_uri)"
```

---

### Quick Reference Table

| Action                        | Command                                                      |
|-------------------------------|-------------------------------------------------------------|
| Check current migration       | `uv run alembic current`                                    |
| Apply all migrations          | `uv run alembic upgrade head`                               |
| Create new migration          | `uv run alembic revision --autogenerate -m "description"`   |
| View migration history        | `uv run alembic history`                                    |
| Downgrade last migration      | `uv run alembic downgrade -1`                               |
| Reset database (dev only)     | `uv run alembic downgrade base && uv run alembic upgrade head` |

### Creating Admin Users

Create an admin user with the CLI command:

```bash
uv run python command.py create-admin
```

This will prompt for:
- Email address
- Full name
- Password (securely hashed with bcrypt)

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your specific values:
   - Set a secure `SECRET_KEY` for production
   - Configure `ALLOWED_ORIGINS` for CORS
   - Adjust `LOG_LEVEL` and other settings as needed

3. The server will automatically load environment variables from the `.env` file.

## Testing

1. Install dependencies for both the backend and the test environment

   ```bash
   uv sync --dev
   ```

## Code Quality: Pre-commit Hooks with Ruff and Bandit

This project uses [pre-commit](https://pre-commit.com/), [Ruff](https://docs.astral.sh/ruff/), and [Bandit](https://bandit.readthedocs.io/) for comprehensive code quality and security checks.

### Setup

To ensure code quality and consistency, please set up pre-commit hooks after cloning the repository:

```bash
# 1. Install dependencies (if not already done)
uv sync --dev

# 2. Install pre-commit hooks
uv run pre-commit install

# 3. Install pre-push hooks (for Bandit security checks)
uv run pre-commit install --hook-type pre-push

# 4. (Optional) Run all hooks on all files to check/fix issues
uv run pre-commit run --all-files
```

### Tools

- **Ruff**: Automatically checks and fixes code style, linting, and import order on every commit
- **Bandit**: Runs security vulnerability scans before each push to identify common security issues

### Manual Checks

You can also run these tools manually:

```bash
# Run Ruff (formatting and linting)
uv run ruff format src/
uv run ruff check src/ --fix

# Run Bandit (security checks)
uv run bandit -r src/
# Or use the convenience script
bash scripts/bandit.sh

# Run all linting and security checks
bash scripts/lint.sh
```

## Running the FastAPI App

This project uses a hybrid structure with the main app at the root level for easy development:

```bash
# Run with uv (recommended)
uv run python main.py

# Or run uvicorn directly
uvicorn app:app --reload
```

- The API docs (Swagger UI) will be available at: http://localhost:8000/docs
- The health endpoint: http://localhost:8000/api/v1/health

## Makefile Commands

This project includes a `Makefile` to simplify common development tasks.

- `make help`: Display a list of all available commands.
- `make lint`: Run the full suite of code quality checks, including formatting, linting, and security vulnerability scanning.
- `make bandit`: Run Bandit security vulnerability checks specifically.
- `make run`: Start the FastAPI development server with hot-reloading.

## 📚 Documentation

For detailed documentation on specific topics, see the [docs/](./docs/) directory:

- **[Production Checklist](./docs/PRODUCTION_CHECKLIST.md)** - 🚀 Production readiness checklist
- **[Security Headers](./docs/SECURITY_HEADERS.md)** - Comprehensive security headers implementation
- **[Class-Based Views](./docs/CBV_README.md)** - FastAPI CBV implementation guide
- **[Database Setup](./docs/DATABASE_SETUP.md)** - Database configuration and migrations
- **[Documentation Index](./docs/README.md)** - Complete documentation overview

### 🔍 Production Readiness

Before deploying to production, run the audit script:

```bash
# Check production readiness
uv run python scripts/production_audit.py
```
