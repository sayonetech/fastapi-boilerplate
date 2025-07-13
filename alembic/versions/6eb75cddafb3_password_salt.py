"""password salt

Revision ID: 6eb75cddafb3
Revises: 4358ef05cf7c
Create Date: 2025-07-12 23:02:11.148653

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6eb75cddafb3"
down_revision: str | Sequence[str] | None = "4358ef05cf7c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new password fields first
    op.add_column("accounts", sa.Column("password", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("accounts", sa.Column("password_salt", sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # Note: Existing users will need to reset their passwords as we're changing
    # from bcrypt to SHA-256+salt hashing. The old hashed_password field
    # cannot be converted automatically.

    # Drop the old hashed_password column
    op.drop_column("accounts", "hashed_password")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the old hashed_password column
    op.add_column("accounts", sa.Column("hashed_password", sa.VARCHAR(), autoincrement=False, nullable=True))

    # Drop the new password fields
    op.drop_column("accounts", "password_salt")
    op.drop_column("accounts", "password")
