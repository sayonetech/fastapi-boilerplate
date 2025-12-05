# Beco Madcrow

[![Quality Gate Status](https://sonarqube.sayone.team/api/project_badges/measure?project=madcrow-backend&metric=alert_status&token=sqb_28e49476b790a9450fd7cdec5cddda4f8727d262)](https://sonarqube.sayone.team/dashboard?id=madcrow-backend)

## Usage

1. Start the docker-compose stack

   The backend require Redis and Postgres which can be started together using `docker-compose`.

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
   curl -LsSf https://astral.sh/uv/install.sh | sh
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

#### One-Time Setup (Only once per project)

```bash
alembic init alembic
```

> _Initializes the Alembic folder and configuration files. Do this once when setting up migrations for the first time._

#### 1. Check Current Migration State

```bash
uv run alembic current
```

> _Shows the current migration revision applied to the database._

#### 2. Generate and Apply Initial Migration (First-Time Setup)

```bash
uv run alembic revision --autogenerate -m "initial schema"
```

> _Generates the initial migration based on your current models._

```bash
uv run alembic upgrade head
```

> _This applies all migrations to bring your database schema up to date._

#### 3. Create a New Migration After Changing Models

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

> _Replace `"describe your change"` with a meaningful message like "add user table" or "add email index"._

#### 4. Apply New Migrations

```bash
uv run alembic upgrade head
```

> _Apply any new migrations to the database._

#### 5. View Migration History

```bash
uv run alembic history
```

> _Shows all available migrations and their status._

#### 6. Downgrade (Undo) the Last Migration

```bash
uv run alembic downgrade -1
```

> _You can also downgrade to a specific revision by replacing `-1` with the revision ID._

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

| Action                    | Command                                                        |
| ------------------------- | -------------------------------------------------------------- |
| Check current migration   | `uv run alembic current`                                       |
| Apply all migrations      | `uv run alembic upgrade head`                                  |
| Create new migration      | `uv run alembic revision --autogenerate -m "description"`      |
| View migration history    | `uv run alembic history`                                       |
| Downgrade last migration  | `uv run alembic downgrade -1`                                  |
| Reset database (dev only) | `uv run alembic downgrade base && uv run alembic upgrade head` |

### Creating Admin Users

Create an admin user with the CLI command:

```bash
uv run python command.py create-admin
```

This will prompt for:

- Email address
- Full name
- Password (securely hashed with SHA-256 + salt)

For more CLI commands and detailed usage, see the [Commands Documentation](docs/commands.md).

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

## 🔧 Development Tools

### Makefile Commands

This project includes a `Makefile` to simplify common development tasks.

- `make help`: Display a list of all available commands.
- `make lint`: Run the full suite of code quality checks, including formatting, linting, and security vulnerability scanning.
- `make bandit`: Run Bandit security vulnerability checks specifically.
- `make run`: Start the FastAPI development server with hot-reloading.

### 🪝 Pre-commit Hooks

This project uses comprehensive pre-commit hooks to ensure code quality, security, and consistency. The hooks are automatically run before each commit and push.

#### **Installation**

Pre-commit hooks are automatically installed when you run:

```bash
uv sync --dev
uv run pre-commit install
```

#### **Hook Categories**

**🔍 Code Quality & Formatting**

- **Ruff**: Fast Python linter and formatter
- **isort**: Import sorting and organization
- **autoflake**: Remove unused imports and variables
- **pyupgrade**: Upgrade Python syntax to newer versions
- **Prettier**: Format YAML, Markdown, and JSON files

**🔒 Security & Vulnerability Scanning**

- **Bandit**: Security vulnerability scanner for Python
- **Safety**: Dependency vulnerability auditing
- **detect-secrets**: Prevent secrets from being committed
- **pip-audit**: Check for known vulnerabilities in dependencies

**📝 Type Checking & Code Analysis**

- **MyPy**: Static type checking
- **Flake8**: Code style and complexity analysis
  - flake8-bugbear: Additional bug and design problem checks
  - flake8-comprehensions: List/dict comprehension checks
  - flake8-simplify: Code simplification suggestions

**📋 File & Syntax Validation**

- **File format checks**: JSON, YAML, TOML, XML validation
- **Syntax checks**: Python AST validation
- **File integrity**: Large file detection, merge conflict detection
- **Dockerfile linting**: Hadolint for Docker best practices

#### **Hook Execution Stages**

**Pre-commit (runs on every commit):**

- File format validation
- Code formatting (Ruff, isort, Prettier)
- Secret detection
- Basic syntax checks

**Pre-push (runs before pushing):**

- Type checking (MyPy)
- Security scanning (Bandit, Safety)
- Comprehensive linting (Flake8)
- Dependency auditing (pip-audit)

#### **Manual Execution**

```bash
# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files
uv run pre-commit run mypy --all-files

# Run only pre-push hooks
uv run pre-commit run --hook-stage pre-push --all-files

# Update hook versions
uv run pre-commit autoupdate
```

#### **Configuration Files**

- **`.pre-commit-config.yaml`**: Hook configuration
- **`.secrets.baseline`**: Baseline for secret detection
- **`pyproject.toml`**: Tool configurations (Ruff, Bandit, etc.)

#### **Bypassing Hooks (Use Sparingly)**

```bash
# Skip pre-commit hooks (not recommended)
git commit --no-verify -m "commit message"

# Skip specific hooks
SKIP=mypy git commit -m "commit message"
```

#### **Troubleshooting**

**Common Issues:**

1. **Hook failures**: Check the output and fix the reported issues
2. **Type checking errors**: Add type hints or update MyPy configuration
3. **Security warnings**: Review and address or add to ignore lists
4. **Dependency conflicts**: Update dependencies or adjust hook versions

**Getting Help:**

```bash
# Check hook status
uv run pre-commit --version

# Validate configuration
uv run pre-commit validate-config

# Clean hook cache
uv run pre-commit clean
```

## 📚 Documentation

For detailed documentation on specific topics, see the [docs/](./docs/) directory:

### 📖 Core Documentation

- **[Documentation Index](./docs/README.md)** - Complete documentation overview and navigation
- **[Getting Started](./docs/getting-started.md)** - Quick start guide for new developers
- **[Commands](./docs/commands.md)** - CLI commands and usage

### 🏗️ Development & Architecture

- **[Event System](./docs/events.md)** - Event-driven architecture with Blinker signals
- **[Class-Based Views](./docs/class-based-views.md)** - FastAPI CBV implementation guide
- **[Database Setup](./docs/database-setup.md)** - Database configuration and migrations
- **[Redis Extension](./docs/redis-extension.md)** - Redis integration and configuration
- **[Error Handling](./docs/error-handling.md)** - Error handling patterns and best practices

### 🔐 Authentication & Security

- **[Authentication](./docs/authentication.md)** - Authentication system overview and implementation
- **[Login Decorator](./docs/login-decorator.md)** - Login decorator usage and patterns
- **[Protection System](./docs/protection-system.md)** - Class-level and method-level protection system
- **[Security Headers](./docs/security-headers.md)** - Comprehensive security headers implementation

### 🚀 Production & API

- **[Production Checklist](./docs/production-checklist.md)** - Production readiness checklist
- **[API Reference](./docs/api-reference.md)** - API endpoints and usage documentation
- **[Profile API](./docs/profile-api.md)** - User profile management endpoints

### 🔍 Production Readiness

Before deploying to production, run the audit script:

```bash
# Check production readiness
uv run python scripts/production_audit.py
```
