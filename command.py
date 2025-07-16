import getpass
import logging
from datetime import datetime

import click
from sqlmodel import Session, create_engine, select

from src.configs import madcrow_config
from src.entities.account import Account
from src.entities.status import AccountStatus
from src.libs.password import create_password_hash, validate_password_strength

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
    """Create an admin user with secure password hashing."""
    password = getpass.getpass("Admin password: ")

    # Validate password strength
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        click.echo(f"❌ Password validation failed: {error_message}")
        return

    # Create password hash and salt using secure method
    hashed_password, password_salt = create_password_hash(password)

    engine = create_engine(
        madcrow_config.sqlalchemy_database_uri,  # type: ignore
        **madcrow_config.sqlalchemy_engine_options,  # type: ignore
    )
    with Session(engine) as session:
        # Check if user already exists
        statement = select(Account).where(Account.email == email.lower())
        existing_user = session.exec(statement).first()

        if existing_user:
            click.echo(f"❌ User with email '{email}' already exists!")
            return

        # Create admin account with secure password fields
        admin = Account(
            name=name.strip(),
            email=email.strip().lower(),
            password=hashed_password,
            password_salt=password_salt,
            is_admin=True,
            status=AccountStatus.ACTIVE,
            timezone="UTC",
            initialized_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        session.add(admin)
        session.commit()
        click.echo(f"✅ Admin user '{email}' created successfully!")
        click.echo(f"   Name: {name}")
        click.echo(f"   Email: {email}")
        click.echo(f"   Status: {AccountStatus.ACTIVE.value}")
        click.echo("   Admin: Yes")
        click.echo("   Password: Securely hashed with salt")


@cli.command()
def list_users():
    """List all users in the database."""
    engine = create_engine(
        madcrow_config.sqlalchemy_database_uri,  # type: ignore
        **madcrow_config.sqlalchemy_engine_options,  # type: ignore
    )
    with Session(engine) as session:
        statement = select(Account).where(Account.is_deleted == False)
        users = session.exec(statement).all()

        if not users:
            click.echo("No users found in the database.")
            return

        click.echo(f"Found {len(users)} user(s):")
        click.echo("-" * 80)

        for user in users:
            click.echo(f"ID: {user.id}")
            click.echo(f"Name: {user.name}")
            click.echo(f"Email: {user.email}")
            click.echo(f"Status: {user.status.value}")
            click.echo(f"Admin: {'Yes' if user.is_admin else 'No'}")
            click.echo(f"Password Set: {'Yes' if user.is_password_set else 'No'}")
            click.echo(f"Can Login: {'Yes' if user.can_login else 'No'}")
            click.echo(f"Last Login: {user.last_login_at or 'Never'}")
            click.echo(f"Created: {user.created_at}")
            click.echo("-" * 80)


@cli.command()
@click.option("--email", prompt=True, help="User email")
def reset_password(email):
    """Reset password for an existing user."""
    engine = create_engine(
        madcrow_config.sqlalchemy_database_uri,  # type: ignore
        **madcrow_config.sqlalchemy_engine_options,  # type: ignore
    )
    with Session(engine) as session:
        # Find user by email
        statement = select(Account).where(Account.email == email.lower())
        user = session.exec(statement).first()

        if not user:
            click.echo(f"❌ User with email '{email}' not found!")
            return

        click.echo(f"Found user: {user.name} ({user.email})")
        new_password = getpass.getpass("New password: ")

        # Validate password strength
        is_valid, error_message = validate_password_strength(new_password)
        if not is_valid:
            click.echo(f"❌ Password validation failed: {error_message}")
            return

        # Create new password hash and salt
        hashed_password, password_salt = create_password_hash(new_password)

        # Update user password
        user.password = hashed_password
        user.password_salt = password_salt
        session.commit()

        click.echo(f"✅ Password reset successfully for '{email}'!")
        click.echo("   User can now login with the new password.")


if __name__ == "__main__":
    cli()
