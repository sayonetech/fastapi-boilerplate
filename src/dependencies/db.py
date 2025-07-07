from collections.abc import Generator

from sqlmodel import Session

from src.extensions.ext_db import db_engine


def get_session() -> Generator[Session, None, None]:
    engine = db_engine.get_engine()
    with Session(engine) as session:
        yield session
