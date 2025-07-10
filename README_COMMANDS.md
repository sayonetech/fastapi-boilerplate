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

````bash
# Show all available commands
uv run python madcrow --help

# Run with verbose logging
uv run python madcrow --verbose status



## Adding New Commands

To add new commands, edit the `command.py` file and add new Click commands:

```python
@cli.command()
@click.option('--option', '-o', help='Option description')
def your_command(option: str):
    """Your command description."""
    click.echo(f"Running your command with option: {option}")
    # Your command logic here
````

## Project Structure

```
madcrow-backend/
├── command.py          # CLI commands using Click
├── madcrow            # CLI entry point script
├── src/               # Application source code
└── README_COMMANDS.md # This documentation
```
