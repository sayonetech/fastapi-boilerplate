import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session

from src.extensions.ext_db import db_engine

logger = logging.getLogger(__name__)


def get_session() -> Generator[Session, None, None]:
    """
    Database session dependency with proper error handling and logging.

    Yields:
        Session: SQLModel database session

    Raises:
        HTTPException: If database connection fails
    """
    try:
        engine = db_engine.get_engine()

        with Session(engine) as session:
            logger.debug("Database session created")
            try:
                yield session
                logger.debug("Database session completed successfully")
            except Exception:
                logger.exception("Database session error")
                session.rollback()
                # Re-raise the original exception so route handlers can catch it
                raise
            finally:
                logger.debug("Database session closed")

    except RuntimeError as e:
        logger.exception("Failed to get database engine")
        raise HTTPException(status_code=503, detail="Database service unavailable") from e
    except Exception as e:
        logger.exception("Database session creation failed")
        raise HTTPException(status_code=500, detail="Internal database error") from e


def get_session_no_exception() -> Generator[Session | None, None, None]:
    """
    Database session dependency that returns None on failure instead of raising.

    Useful for optional database operations or health checks.

    Yields:
        Session | None: SQLModel database session or None if connection fails
    """
    try:
        logger.debug("Attempting to get database engine for optional session")
        engine = db_engine.get_engine()
        logger.debug("Database engine obtained, creating session")
        with Session(engine) as session:
            logger.debug("Optional database session created successfully")
            yield session
            logger.debug("Optional database session completed")
    except RuntimeError as e:
        logger.warning(f"Database engine not available for optional session: {e}")
        yield None
    except Exception as e:
        logger.warning(f"Database session creation failed (non-critical): {e}")
        yield None


# Type aliases for dependency injection
DatabaseSession = Annotated[Session, Depends(get_session)]
OptionalDatabaseSession = Annotated[Session | None, Depends(get_session_no_exception)]
