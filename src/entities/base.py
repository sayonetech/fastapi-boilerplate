# This acts as the common base class for all SQLModel tables.
from sqlmodel import SQLModel


class Base(SQLModel):
    """Common base for all models. Useful for shared logic."""
