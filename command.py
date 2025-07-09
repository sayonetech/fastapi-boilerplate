"""CLI commands for Madcrow Backend using Click."""

import getpass
import logging
import sys
from pathlib import Path

import bcrypt
import click
from sqlmodel import Session, create_engine, select

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.configs import madcrow_config
from src.entities.account import Account
from src.entities.status import AccountStatus


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Configure logging for CLI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """Madcrow Backend CLI commands."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@cli.command()
def version():
    """Show application version."""
    click.echo(f"Madcrow Backend v{madcrow_config.APP_VERSION}")


@cli.command()
def help():
    """Show this help message."""
    ctx = click.get_current_context()
    click.echo(ctx.get_help())


@cli.command()
@click.option("--email", prompt=True, help="Admin email")
@click.option("--name", prompt=True, help="Admin name")
def create_admin(email, name):
    """Create an admin user with properly hashed password."""
    password = getpass.getpass("Admin password: ")

    # Hash the password
    hashed_password = hash_password(password)

    engine = create_engine(
        madcrow_config.sqlalchemy_database_uri,  # type: ignore
        **madcrow_config.sqlalchemy_engine_options,  # type: ignore
    )
    with Session(engine) as session:
        # Check if user already exists
        statement = select(Account).where(Account.email == email)
        existing_user = session.exec(statement).first()

        if existing_user:
            click.echo(f"❌ User with email '{email}' already exists!")
            return

        admin = Account(
            name=name,
            email=email,
            hashed_password=hashed_password,
            is_admin=True,
            status=AccountStatus.ACTIVE
        )
        session.add(admin)
        session.commit()
        click.echo(f"✅ Admin user '{email}' created successfully with hashed password!")


if __name__ == "__main__":
    cli()
