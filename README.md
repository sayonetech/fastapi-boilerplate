# Beco Madcrow
----------------
## Usage

1. Start the docker-compose stack

   The backend require Redis which can be started together using `docker-compose`.

   ```bash
   Please add code here later
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

6. Start backend

   ```bash
   uv run python main.py
   ```

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
