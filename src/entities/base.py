# base.py
from datetime import datetime
from uuid import UUID

from sqlalchemy import MetaData, func
from sqlmodel import Field, SQLModel

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

custom_metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)


class Base(SQLModel, metadata=custom_metadata):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.current_timestamp()},
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={
            "server_default": func.current_timestamp(),
            "onupdate": func.current_timestamp(),
        },
        nullable=False,
    )
    created_by: UUID | None = Field(
        default=None,
        foreign_key="accounts.id",
        nullable=True,
    )
