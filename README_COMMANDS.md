# Madcrow Backend CLI Commands

This document describes the CLI command system for Madcrow Backend using Click.

## Usage

Run commands using the `madcrow` script:

```bash
uv run python madcrow [COMMAND] [OPTIONS]
```

## Available Commands

### Basic Commands

#### `print-message`
Print a custom message.

```bash
uv run python madcrow print-message --message "Hello World!"
uv run python madcrow print-message -m "Hello World!"
```

#### `status`
Show system status information.

```bash
uv run python madcrow status
```

#### `version`
Show application version.

```bash
uv run python madcrow version
```

#### `help`
Show help message.

```bash
uv run python madcrow help
```


### Database Commands

#### `db-backup`
Create a database backup.

```bash
uv run python madcrow db-backup
uv run python madcrow db-backup --name my_backup
uv run python madcrow db-backup -n my_backup
```

#### `migrate`
Run database migrations.

```bash
uv run python madcrow migrate                    # Run all migrations
uv run python madcrow migrate --type users       # Run user migrations
uv run python madcrow migrate -t data            # Run data migrations
```




### System Commands

#### `cache-clear`
Clear application cache.

```bash
uv run python madcrow cache-clear                # Clear all cache
uv run python madcrow cache-clear --type session # Clear session cache
uv run python madcrow cache-clear -t data        # Clear data cache
```

#### `maintenance`
Run system maintenance tasks.

```bash
uv run python madcrow maintenance                    # Run all maintenance tasks
uv run python madcrow maintenance --tasks cleanup   # Run cleanup only
uv run python madcrow maintenance -t optimize       # Run optimization only
uv run python madcrow maintenance -t cleanup,validate # Run specific tasks
```

#### `create-admin`
Create an admin user in the database.

```bash
uv run python madcrow create-admin
```

This command will prompt for admin name, email, and password (stored as plain text; hash in production).


## Global Options

- `--verbose, -v`: Enable verbose logging
- `--help`: Show help message

## Examples

```bash
# Show all available commands
uv run python madcrow --help

# Run with verbose logging
uv run python madcrow --verbose status

# Create a backup with custom name
uv run python madcrow db-backup --name production_backup_2024

# Run user migrations
uv run python madcrow migrate --type users

# Clear session cache
uv run python madcrow cache-clear --type session

# Run maintenance tasks
uv run python madcrow maintenance --tasks cleanup,optimize
```

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

## Project Structure

```
madcrow-backend/
├── command.py          # CLI commands using Click
├── madcrow            # CLI entry point script
├── src/               # Application source code
└── README_COMMANDS.md # This documentation
```
