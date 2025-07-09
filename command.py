"""CLI commands for Madcrow Backend using Click."""

import getpass
import logging

import click
from sqlmodel import Session, create_engine

from configs.enviornment.db_config import DatabaseConfig
from entities.account import Account
from entities.status import AccountStatus

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
    from src.configs import madcrow_config

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
    """Create an admin user (password stored as plain text; hash in production!)."""
    password = getpass.getpass("Admin password: ")
    db_config = DatabaseConfig()
    engine = create_engine(
        db_config.SQLALCHEMY_DATABASE_URI,  # type: ignore
        **db_config.SQLALCHEMY_ENGINE_OPTIONS,  # type: ignore
    )
    with Session(engine) as session:
        admin = Account(name=name, email=email, hashed_password=password, is_admin=True, status=AccountStatus.ACTIVE)
        session.add(admin)
        session.commit()
        click.echo(f"✅ Admin user '{email}' created. (Password is stored as plain text!)")


if __name__ == "__main__":
    cli()
