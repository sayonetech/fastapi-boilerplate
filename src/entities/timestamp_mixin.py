from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field


class TimestampMixin:
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column_kwargs={"server_default": func.current_timestamp()}, nullable=False
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.current_timestamp(), "onupdate": func.current_timestamp()},
        nullable=False,
    )

    # To be set ,apart from admin
    # created_by: Optional[UUID] = Field(
    #     default=None,
    #     foreign_key="accounts.id"
    # )
