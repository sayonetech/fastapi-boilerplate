from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from entities.status import AccountStatus


class Account(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    status: AccountStatus
    timezone: str | None = None
    avatar: str | None = None
    is_admin: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    initialized_at: datetime | None = None
    activation_token: str | None = None
    token_expires_at: datetime | None = None

    class Config:
        from_attributes = True  # Allows conversion from ORM/SQLModel objects
