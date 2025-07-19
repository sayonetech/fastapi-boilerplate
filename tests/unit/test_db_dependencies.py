"""Unit tests for database dependencies - Fixed version."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from src.dependencies.db import get_db_session, get_session, get_session_no_exception


@pytest.mark.unit
class TestDatabaseDependencies:
    """Test database dependency functions."""

    @pytest.fixture
    def mock_engine(self):
        """Create mock database engine."""
        engine = Mock()
        return engine

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock()
        session.close = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.begin = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        return session

    @patch("src.dependencies.db.Session")
    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_session_success(self, mock_get_engine, mock_session_class, mock_engine, mock_session):
        """Test successful database session creation."""
        mock_get_engine.return_value = mock_engine
        mock_session_class.return_value = mock_session

        # Test the generator
        session_gen = get_session()
        session = next(session_gen)

        assert session == mock_session
        mock_get_engine.assert_called_once()
        mock_session_class.assert_called_once_with(mock_engine)

        # Test cleanup
        try:
            next(session_gen)
        except StopIteration:
            pass

        mock_session.__exit__.assert_called_once()

    @patch("src.dependencies.db.Session")
    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_session_with_exception_during_use(
        self, mock_get_engine, mock_session_class, mock_engine, mock_session
    ):
        """Test session cleanup when exception occurs during use."""
        mock_get_engine.return_value = mock_engine
        mock_session_class.return_value = mock_session

        session_gen = get_session()
        session = next(session_gen)

        # Simulate exception during session use
        try:
            session_gen.throw(Exception("Database operation failed"))
        except Exception:
            pass

        mock_session.rollback.assert_called_once()
        mock_session.__exit__.assert_called_once()

    @patch("src.dependencies.db.Session")
    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_session_close_exception(self, mock_get_engine, mock_session_class, mock_engine, mock_session):
        """Test session cleanup when __exit__ raises exception."""
        mock_get_engine.return_value = mock_engine
        # Make Session() raise exception when called
        mock_session_class.side_effect = Exception("Close failed")

        session_gen = get_session()
        with pytest.raises(HTTPException) as exc_info:
            next(session_gen)

        assert exc_info.value.status_code == 500
        assert "Internal database error" in str(exc_info.value.detail)

    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_session_creation_failure(self, mock_get_engine):
        """Test session creation failure."""
        mock_get_engine.side_effect = RuntimeError("Connection failed")

        session_gen = get_session()
        with pytest.raises(HTTPException) as exc_info:
            next(session_gen)

        assert exc_info.value.status_code == 503
        assert "Database service unavailable" in str(exc_info.value.detail)

    @patch("src.dependencies.db.Session")
    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_session_multiple_iterations(self, mock_get_engine, mock_session_class, mock_engine, mock_session):
        """Test that session generator only yields once."""
        mock_get_engine.return_value = mock_engine
        mock_session_class.return_value = mock_session

        session_gen = get_session()

        # First iteration should yield session
        session = next(session_gen)
        assert session == mock_session

        # Second iteration should raise StopIteration
        with pytest.raises(StopIteration):
            next(session_gen)

        mock_session.__exit__.assert_called_once()

    @patch("src.dependencies.db.Session")
    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_session_no_exception_success(self, mock_get_engine, mock_session_class, mock_engine, mock_session):
        """Test successful database session creation without exceptions."""
        mock_get_engine.return_value = mock_engine
        mock_session_class.return_value = mock_session

        session_gen = get_session_no_exception()
        session = next(session_gen)

        assert session == mock_session
        mock_get_engine.assert_called_once()

        # Test cleanup
        try:
            next(session_gen)
        except StopIteration:
            pass

        mock_session.__exit__.assert_called_once()

    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_session_no_exception_with_failure(self, mock_get_engine):
        """Test database session creation failure returns None."""
        mock_get_engine.side_effect = RuntimeError("Connection failed")

        session_gen = get_session_no_exception()
        session = next(session_gen)

        assert session is None

    @patch("src.dependencies.db.Session")
    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_db_session_success(self, mock_get_engine, mock_session_class, mock_engine, mock_session):
        """Test get_db_session function."""
        mock_get_engine.return_value = mock_engine
        mock_session_class.return_value = mock_session

        session_gen = get_db_session()
        session = next(session_gen)

        assert session == mock_session

    @patch("src.dependencies.db.Session")
    @patch("src.dependencies.db.db_engine.get_engine")
    def test_get_db_session_with_exception(self, mock_get_engine, mock_session_class, mock_engine, mock_session):
        """Test get_db_session with exception."""
        mock_get_engine.return_value = mock_engine
        # Make Session() raise exception when called
        mock_session_class.side_effect = Exception("Close failed")

        session_gen = get_db_session()
        with pytest.raises(HTTPException) as exc_info:
            next(session_gen)

        assert exc_info.value.status_code == 500
        assert "Internal database error" in str(exc_info.value.detail)
