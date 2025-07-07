from datetime import datetime
from typing import Optional

from sqlmodel import Field

from .base import BaseModel


class Account(BaseModel, table=True):
    __tablename__ = "accounts"

    name: str = Field(nullable=False, max_length=255)
    email: str = Field(nullable=False, unique=True, index=True, max_length=255)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    last_login_at: Optional[datetime] = Field(default=None)
    last_login_ip: Optional[str] = Field(default=None, max_length=255)
    avatar: Optional[str] = Field(default=None, max_length=255)
    timezone: Optional[str] = Field(default=None, max_length=255)

    is_admin: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
