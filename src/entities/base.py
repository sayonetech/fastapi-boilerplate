import uuid
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"server_default": func.current_timestamp()},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"server_default": func.current_timestamp(), "onupdate": func.current_timestamp()},
    )
    created_by: Optional[UUID] = Field(default=None, foreign_key="accounts.id")


class BaseModel(SQLModel, TimestampMixin, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
