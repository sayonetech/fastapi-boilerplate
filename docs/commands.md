# CLI Commands

This document describes the command-line interface (CLI) commands available in the Madcrow Backend project for administration and management tasks.

## Usage

Run commands using the `command.py` script:

```bash
uv run python command.py [COMMAND] [OPTIONS]
```

## Available Commands

### Administrative Commands

#### `create-admin`

Create an admin user account with secure password hashing.

**Usage:**

```bash
uv run python command.py create-admin
```

**Options:**

- `--email TEXT`: Admin email address (will prompt if not provided)
- `--name TEXT`: Admin full name (will prompt if not provided)
- `--help`: Show help message

**Interactive Mode:**

```bash
uv run python command.py create-admin
# Prompts:
# Admin email: admin@example.com
# Admin name: Admin User
# Admin password: [hidden input]
```

**With Parameters:**

```bash
uv run python command.py create-admin --email admin@example.com --name "Admin User"
# Will still prompt for password securely
```

**Features:**

- Secure password input (hidden from terminal)
- Password strength validation (minimum 8 characters, letters + digits)
- SHA-256 + salt password hashing
- Duplicate email detection
- Account status set to ACTIVE
- Admin privileges automatically granted

This command will prompt for admin name, email, and password (securely hashed with SHA-256 + salt).

## Global Options

- `--help`: Show help message for any command

## Examples

```bash
# Show all available commands
uv run python command.py --help

# Show help for specific command
uv run python command.py create-admin --help

# Create admin user interactively
uv run python command.py create-admin

# Create admin user with email parameter
uv run python command.py create-admin --email admin@example.com --name "Admin User"
```

## Password Requirements

When creating admin users, passwords must meet these requirements:

- **Minimum Length**: 8 characters
- **Maximum Length**: 128 characters
- **Required Characters**: At least one letter and one digit
- **Forbidden**: Common weak passwords (password, 123456, etc.)

## Security Features

- **Secure Input**: Password input is hidden from terminal
- **Strong Hashing**: SHA-256 with unique salt per password
- **Validation**: Email format and password strength validation
- **Duplicate Prevention**: Prevents creating users with existing emails

## Adding New Commands

To add new commands, edit the `command.py` file and add new Click commands:

```python
@cli.command()
@click.option('--option', '-o', help='Option description')
def your_command(option: str):
    """Your command description."""
    click.echo(f"Running your command with option: {option}")
    # Your command logic here
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. Ensure PostgreSQL is running
2. Check database credentials in `.env` file
3. Verify database exists: `createdb madcrow`
4. Run migrations: `uv run alembic upgrade head`

### Permission Issues

If you get permission errors:

1. Check file permissions: `chmod +x command.py`
2. Ensure virtual environment is activated
3. Install dependencies: `uv sync`

### Password Validation Errors

If password validation fails:

- Use at least 8 characters
- Include both letters and numbers
- Avoid common passwords like "password123"

## Related Documentation

- [Getting Started Guide](./getting-started.md) - Complete setup instructions
- [Authentication System](./authentication.md) - Authentication details
- [Database Setup](./DATABASE_SETUP.md) - Database configuration
