"""Unit tests for SessionService."""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from src.dependencies.redis import RedisService
from src.entities.account import Account, AccountStatus
from src.models.auth import SessionInfo, UserProfile
from src.services.session_service import SessionService


@pytest.mark.unit
class TestSessionService:
    """Test SessionService functionality."""

    @pytest.fixture
    def mock_redis_service(self):
        """Create mock Redis service."""
        return Mock(spec=RedisService)

    @pytest.fixture
    def session_service(self, mock_redis_service):
        """Create SessionService instance with mocked Redis."""
        return SessionService(mock_redis_service)

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return Account(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",  # pragma: allowlist secret
            status=AccountStatus.ACTIVE,
            is_admin=False,
            timezone="UTC",
            avatar=None,
            last_login_at=None,
            initialized_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def test_init(self, mock_redis_service):
        """Test SessionService initialization."""
        service = SessionService(mock_redis_service)
        assert service.redis == mock_redis_service
        assert service.DEFAULT_SESSION_DURATION == 24 * 60 * 60
        assert service.REMEMBER_ME_DURATION == 30 * 24 * 60 * 60
        assert service.SESSION_KEY_PREFIX == "session:"
        assert service.USER_SESSIONS_PREFIX == "user_sessions:"

    @patch("src.services.session_service.uuid4")
    @patch("src.services.session_service.datetime")
    def test_create_session_success(self, mock_datetime, mock_uuid4, session_service, sample_user):
        """Test successful session creation."""
        # Setup mocks
        mock_uuid4.return_value.hex = "test_session_id"
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        session_service.redis.set_session.return_value = True
        session_service.redis.get_cache.return_value = None
        session_service.redis.set_cache.return_value = True

        # Test
        result = session_service.create_session(sample_user, remember_me=False, login_ip="192.168.1.1")

        # Assertions
        assert isinstance(result, SessionInfo)
        assert result.session_id == "sess_test_session_id"
        assert result.remember_me is False
        assert result.expires_at == mock_now + timedelta(seconds=session_service.DEFAULT_SESSION_DURATION)

        # Verify Redis calls
        session_service.redis.set_session.assert_called_once()
        session_data = session_service.redis.set_session.call_args[0][1]
        assert session_data["user_id"] == str(sample_user.id)
        assert session_data["email"] == sample_user.email
        assert session_data["login_ip"] == "192.168.1.1"

    @patch("src.services.session_service.uuid4")
    @patch("src.services.session_service.datetime")
    def test_create_session_remember_me(self, mock_datetime, mock_uuid4, session_service, sample_user):
        """Test session creation with remember_me option."""
        # Setup mocks
        mock_uuid4.return_value.hex = "test_session_id"
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        session_service.redis.set_session.return_value = True
        session_service.redis.get_cache.return_value = None
        session_service.redis.set_cache.return_value = True

        # Test
        result = session_service.create_session(sample_user, remember_me=True)

        # Assertions
        assert result.remember_me is True
        assert result.expires_at == mock_now + timedelta(seconds=session_service.REMEMBER_ME_DURATION)

        # Verify Redis call with correct duration
        session_service.redis.set_session.assert_called_once()
        call_args = session_service.redis.set_session.call_args
        assert call_args[0][2] == session_service.REMEMBER_ME_DURATION  # duration parameter

    def test_create_session_redis_failure(self, session_service, sample_user):
        """Test session creation when Redis fails."""
        session_service.redis.set_session.return_value = False

        with pytest.raises(RuntimeError, match="Failed to store session in Redis"):
            session_service.create_session(sample_user)

    def test_create_session_exception(self, session_service, sample_user):
        """Test session creation with Redis exception."""
        session_service.redis.set_session.side_effect = Exception("Redis error")

        with pytest.raises(RuntimeError, match="Session creation failed"):
            session_service.create_session(sample_user)

    def test_validate_session_empty_id(self, session_service):
        """Test session validation with empty session ID."""
        assert session_service.validate_session("") is None
        assert session_service.validate_session(None) is None

    @patch("src.services.session_service.datetime")
    def test_validate_session_not_found(self, mock_datetime, session_service):
        """Test session validation when session not found."""
        session_service.redis.get_session.return_value = None

        result = session_service.validate_session("test_session_id")
        assert result is None

    @patch("src.services.session_service.datetime")
    def test_validate_session_expired(self, mock_datetime, session_service):
        """Test session validation when session is expired."""
        # Setup expired session
        past_time = datetime(2023, 1, 1, 12, 0, 0)
        current_time = datetime(2023, 1, 2, 12, 0, 0)  # 1 day later

        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat.return_value = past_time

        session_data = {"expires_at": past_time.isoformat(), "user_id": str(uuid4()), "remember_me": False}
        session_service.redis.get_session.return_value = session_data
        session_service.redis.delete_session.return_value = True

        result = session_service.validate_session("test_session_id")
        assert result is None
        session_service.redis.delete_session.assert_called_once_with("test_session_id")

    @patch("src.services.session_service.datetime")
    def test_validate_session_success(self, mock_datetime, session_service):
        """Test successful session validation."""
        # Setup valid session
        current_time = datetime(2023, 1, 1, 12, 0, 0)
        future_time = datetime(2023, 1, 2, 12, 0, 0)  # 1 day later

        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat.return_value = future_time

        session_data = {
            "expires_at": future_time.isoformat(),
            "user_id": str(uuid4()),
            "remember_me": False,
            "last_activity": current_time.isoformat(),
        }
        session_service.redis.get_session.return_value = session_data

        result = session_service.validate_session("test_session_id")

        assert result is not None
        assert result["last_activity"] == current_time.isoformat()

    def test_validate_session_exception(self, session_service):
        """Test session validation with exception."""
        session_service.redis.get_session.side_effect = Exception("Redis error")

        result = session_service.validate_session("test_session_id")
        assert result is None

    @patch("src.services.session_service.datetime")
    def test_validate_session_remember_me_extension(self, mock_datetime, session_service):
        """Test session validation with remember_me extension."""
        current_time = datetime(2023, 1, 1, 12, 0, 0)
        future_time = datetime(2023, 1, 2, 12, 0, 0)

        mock_datetime.utcnow.return_value = current_time
        mock_datetime.fromisoformat.return_value = future_time

        session_data = {
            "expires_at": future_time.isoformat(),
            "user_id": str(uuid4()),
            "remember_me": True,
            "last_activity": current_time.isoformat(),
        }
        session_service.redis.get_session.return_value = session_data
        session_service.redis.set_session.return_value = True

        result = session_service.validate_session("test_session_id")

        assert result is not None
        # Verify session was extended
        session_service.redis.set_session.assert_called_once()

    def test_delete_session_success(self, session_service):
        """Test successful session deletion."""
        session_data = {"user_id": str(uuid4())}
        session_service.redis.get_session.return_value = session_data
        session_service.redis.delete_session.return_value = True
        session_service.redis.get_cache.return_value = json.dumps(["test_session_id"])
        session_service.redis.set_cache.return_value = True

        result = session_service.delete_session("test_session_id")

        assert result is True
        session_service.redis.delete_session.assert_called_once_with("test_session_id")

    def test_delete_session_not_found(self, session_service):
        """Test session deletion when session not found."""
        session_service.redis.get_session.return_value = None
        session_service.redis.delete_session.return_value = False

        result = session_service.delete_session("test_session_id")

        assert result is False

    def test_delete_session_exception(self, session_service):
        """Test session deletion with exception."""
        session_service.redis.get_session.side_effect = Exception("Redis error")

        result = session_service.delete_session("test_session_id")
        assert result is False

    def test_delete_all_user_sessions_success(self, session_service):
        """Test successful deletion of all user sessions."""
        user_id = uuid4()
        session_ids = ["session1", "session2", "session3"]

        session_service.redis.get_cache.return_value = json.dumps(session_ids)
        session_service.redis.delete_session.return_value = True
        session_service.redis.delete_cache.return_value = True

        result = session_service.delete_all_user_sessions(user_id)

        assert result == 3
        assert session_service.redis.delete_session.call_count == 3

    def test_delete_all_user_sessions_no_sessions(self, session_service):
        """Test deletion when user has no sessions."""
        user_id = uuid4()
        session_service.redis.get_cache.return_value = None

        result = session_service.delete_all_user_sessions(user_id)

        assert result == 0

    def test_delete_all_user_sessions_partial_failure(self, session_service):
        """Test deletion with some sessions failing to delete."""
        user_id = uuid4()
        session_ids = ["session1", "session2", "session3"]

        session_service.redis.get_cache.return_value = json.dumps(session_ids)
        # First two succeed, third fails
        session_service.redis.delete_session.side_effect = [True, True, False]
        session_service.redis.delete_cache.return_value = True

        result = session_service.delete_all_user_sessions(user_id)

        assert result == 2

    def test_delete_all_user_sessions_exception(self, session_service):
        """Test deletion with exception."""
        user_id = uuid4()
        session_service.redis.get_cache.side_effect = Exception("Redis error")

        result = session_service.delete_all_user_sessions(user_id)
        assert result == 0

    def test_get_user_from_session_success(self, session_service):
        """Test successful user profile retrieval from session."""
        user_id = uuid4()
        created_at = datetime(2023, 1, 1, 12, 0, 0)

        session_data = {
            "user_id": str(user_id),
            "name": "Test User",
            "email": "test@example.com",
            "status": "active",
            "timezone": "UTC",
            "avatar": "avatar.jpg",
            "is_admin": False,
            "created_at": created_at.isoformat(),
            "expires_at": (created_at + timedelta(days=1)).isoformat(),
            "remember_me": False,
            "last_activity": created_at.isoformat(),
        }

        session_service.redis.get_session.return_value = session_data

        with patch("src.services.session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = created_at
            mock_datetime.fromisoformat.return_value = created_at + timedelta(days=1)

            result = session_service.get_user_from_session("test_session_id")

        assert isinstance(result, UserProfile)
        assert result.id == user_id
        assert result.name == "Test User"
        assert result.email == "test@example.com"
        assert result.status == "active"
        assert result.is_admin is False

    def test_get_user_from_session_invalid_session(self, session_service):
        """Test user profile retrieval with invalid session."""
        session_service.redis.get_session.return_value = None

        result = session_service.get_user_from_session("invalid_session_id")
        assert result is None

    def test_get_user_from_session_exception(self, session_service):
        """Test user profile retrieval with exception."""
        session_data = {"user_id": "invalid_uuid"}
        session_service.redis.get_session.return_value = session_data

        with patch("src.services.session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1)
            mock_datetime.fromisoformat.return_value = datetime(2023, 1, 2)

            result = session_service.get_user_from_session("test_session_id")

        assert result is None

    def test_extend_session_success(self, session_service):
        """Test successful session extension."""
        session_data = {"expires_at": "2023-01-01T12:00:00"}
        session_service.redis.set_session.return_value = True

        with patch("src.services.session_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)

            session_service._extend_session("test_session_id", session_data)

        session_service.redis.set_session.assert_called_once()
        assert "expires_at" in session_data

    def test_extend_session_exception(self, session_service):
        """Test session extension with exception."""
        session_data = {"expires_at": "2023-01-01T12:00:00"}
        session_service.redis.set_session.side_effect = Exception("Redis error")

        # Should not raise exception
        session_service._extend_session("test_session_id", session_data)

    def test_add_user_session_new_user(self, session_service):
        """Test adding session for new user."""
        user_id = uuid4()
        session_service.redis.get_cache.return_value = None
        session_service.redis.set_cache.return_value = True

        session_service._add_user_session(user_id, "test_session_id", 3600)

        session_service.redis.set_cache.assert_called_once()
        call_args = session_service.redis.set_cache.call_args
        assert json.loads(call_args[0][1]) == ["test_session_id"]

    def test_add_user_session_existing_user(self, session_service):
        """Test adding session for existing user."""
        user_id = uuid4()
        existing_sessions = ["session1", "session2"]
        session_service.redis.get_cache.return_value = json.dumps(existing_sessions)
        session_service.redis.set_cache.return_value = True

        session_service._add_user_session(user_id, "session3", 3600)

        session_service.redis.set_cache.assert_called_once()
        call_args = session_service.redis.set_cache.call_args
        assert json.loads(call_args[0][1]) == ["session1", "session2", "session3"]

    def test_add_user_session_duplicate(self, session_service):
        """Test adding duplicate session."""
        user_id = uuid4()
        existing_sessions = ["session1", "session2"]
        session_service.redis.get_cache.return_value = json.dumps(existing_sessions)
        session_service.redis.set_cache.return_value = True

        session_service._add_user_session(user_id, "session1", 3600)

        # Should not add duplicate
        call_args = session_service.redis.set_cache.call_args
        assert json.loads(call_args[0][1]) == ["session1", "session2"]

    def test_add_user_session_exception(self, session_service):
        """Test adding user session with exception."""
        user_id = uuid4()
        session_service.redis.get_cache.side_effect = Exception("Redis error")

        # Should not raise exception
        session_service._add_user_session(user_id, "test_session_id", 3600)

    def test_remove_user_session_success(self, session_service):
        """Test successful user session removal."""
        user_id = uuid4()
        existing_sessions = ["session1", "session2", "session3"]
        session_service.redis.get_cache.return_value = json.dumps(existing_sessions)
        session_service.redis.set_cache.return_value = True

        session_service._remove_user_session(user_id, "session2")

        session_service.redis.set_cache.assert_called_once()
        call_args = session_service.redis.set_cache.call_args
        assert json.loads(call_args[0][1]) == ["session1", "session3"]

    def test_remove_user_session_last_session(self, session_service):
        """Test removing last user session."""
        user_id = uuid4()
        existing_sessions = ["session1"]
        session_service.redis.get_cache.return_value = json.dumps(existing_sessions)
        session_service.redis.delete_cache.return_value = True

        session_service._remove_user_session(user_id, "session1")

        session_service.redis.delete_cache.assert_called_once()

    def test_remove_user_session_not_found(self, session_service):
        """Test removing non-existent session."""
        user_id = uuid4()
        session_service.redis.get_cache.return_value = None

        # Should not raise exception
        session_service._remove_user_session(user_id, "session1")

    def test_remove_user_session_exception(self, session_service):
        """Test removing user session with exception."""
        user_id = uuid4()
        session_service.redis.get_cache.side_effect = Exception("Redis error")

        # Should not raise exception
        session_service._remove_user_session(user_id, "session1")


@pytest.mark.unit
def test_get_session_service():
    """Test session service factory function."""
    from src.services.session_service import get_session_service

    mock_redis = Mock(spec=RedisService)
    service = get_session_service(mock_redis)

    assert isinstance(service, SessionService)
    assert service.redis == mock_redis
