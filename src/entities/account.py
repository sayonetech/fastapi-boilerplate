from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Session, select

from .base import Base
from .status import AccountStatus


class Account(Base, table=True):
    __tablename__ = "accounts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, index=True)
    password: str | None = Field(default=None)
    password_salt: str | None = Field(default=None)

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

    # test filed to check migration working or not
    # test_unique: str = Field(default=None, unique=True)

    @property
    def is_password_set(self) -> bool:
        """Check if user has a password set."""
        return self.password is not None and self.password_salt is not None

    @property
    def is_active(self) -> bool:
        """Check if account is active and not deleted."""
        return self.status == AccountStatus.ACTIVE and not self.is_deleted

    @property
    def is_pending(self) -> bool:
        """Check if account is pending activation."""
        return self.status == AccountStatus.PENDING

    @property
    def is_banned(self) -> bool:
        """Check if account is banned."""
        return self.status == AccountStatus.BANNED

    @property
    def is_closed(self) -> bool:
        """Check if account is closed."""
        return self.status == AccountStatus.CLOSED

    @property
    def can_login(self) -> bool:
        """Check if user can login (active, not deleted, has password)."""
        return self.is_active and self.is_password_set

    def get_status(self) -> AccountStatus:
        """Get account status as enum."""
        return self.status

    def update_last_login(self, ip_address: str | None = None) -> None:
        """Update last login timestamp and IP."""
        self.last_login_at = datetime.now(UTC)
        if ip_address:
            self.last_login_ip = ip_address

    def activate(self) -> None:
        """Activate the account."""
        self.status = AccountStatus.ACTIVE
        if not self.initialized_at:
            self.initialized_at = datetime.now(UTC)

    def ban(self) -> None:
        """Ban the account."""
        self.status = AccountStatus.BANNED

    def close(self) -> None:
        """Close the account."""
        self.status = AccountStatus.CLOSED

    def soft_delete(self) -> None:
        """Soft delete the account."""
        self.is_deleted = True

    @classmethod
    def get_by_email(cls, session: Session, email: str) -> Optional["Account"]:
        """Get account by email address."""
        statement = select(cls).where(cls.email == email.lower(), cls.is_deleted is False)
        return session.exec(statement).first()

    @classmethod
    def get_active_by_email(cls, session: Session, email: str) -> Optional["Account"]:
        """Get active account by email address."""
        statement = select(cls).where(
            cls.email == email.lower(), cls.status == AccountStatus.ACTIVE, cls.is_deleted is False
        )
        return session.exec(statement).first()

    @classmethod
    def email_exists(cls, session: Session, email: str) -> bool:
        """Check if email already exists."""
        statement = select(cls).where(cls.email == email.lower(), cls.is_deleted is False)
        return session.exec(statement).first() is not None
