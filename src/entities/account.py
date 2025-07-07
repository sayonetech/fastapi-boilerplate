from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field

from entities.base import Base
from entities.status import AccountStatus
from entities.timestamp_mixin import TimestampMixin


# account.py
# This file defines the Account model, which represents user accounts in the system.
class Account(Base, TimestampMixin, table=True):
    __tablename__ = "accounts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, index=True)
    hashed_password: str | None = Field(default=None)

    status: AccountStatus = Field(default=AccountStatus.PENDING, nullable=False)

    timezone: str | None = Field(default=None)
    last_login_at: datetime | None = Field(default=None)
    last_login_ip: str | None = Field(default=None)
    avatar: str | None = Field(default=None)
    initialized_at: datetime | None = Field(default=None)

    is_deleted: bool = Field(default=False, nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    activation_token: str | None = Field(default=None)
    token_expires_at: datetime | None = Field(default=None)
