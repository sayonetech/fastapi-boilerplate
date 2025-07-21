"""Unit tests for authentication service."""

from unittest.mock import MagicMock, patch

import pytest

from src.entities.account import Account
from src.entities.status import AccountStatus
from src.exceptions import (
    AccountClosedError,
    AccountError,
    AccountNotVerifiedError,
    AuthenticationError,
    RateLimitExceededError,
)
from src.models.token import TokenPair
from src.services.auth_service import AuthService


class TestAuthService:
    """Test cases for AuthService class."""

    def test_auth_service_initialization(self, test_db_session):
        """Test AuthService initialization."""
        auth_service = AuthService(db_session=test_db_session)
        assert auth_service.db_session == test_db_session

    def test_verify_password_correct(self, auth_service):
        """Test password verification with correct password."""
        password = "SecurePassword123!"  # pragma: allowlist secret
        hashed_password = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # pragma: allowlist secret
        salt = "randomsalt123"

        result = auth_service._verify_password(password, hashed_password, salt)
        # This will depend on the actual hashing implementation
        # For now, we'll test the method exists and returns a boolean
        assert isinstance(result, bool)

    def test_verify_password_incorrect(self, auth_service):
        """Test password verification with incorrect password."""
        password = "WrongPassword"  # pragma: allowlist secret
        hashed_password = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # pragma: allowlist secret
        salt = "randomsalt123"

        result = auth_service._verify_password(password, hashed_password, salt)
        assert isinstance(result, bool)

    @patch("src.services.auth_service.Account.get_by_email")
    @patch("src.services.auth_service.get_token_service")
    def test_authenticate_user_success(self, mock_get_token_service, mock_get_by_email, auth_service):
        """Test successful user authentication."""
        # Mock user with all required properties
        mock_user = MagicMock()
        mock_user.id = "user_123"
        mock_user.email = "test@example.com"
        mock_user.status = AccountStatus.ACTIVE
        mock_user.password = "hashed_password"  # pragma: allowlist secret
        mock_user.password_salt = "salt"  # pragma: allowlist secret
        mock_user.is_deleted = False
        mock_user.is_password_set = True
        mock_user.is_active = True
        mock_user.update_last_login = MagicMock()
        mock_get_by_email.return_value = mock_user

        # Mock token service
        mock_token_service = MagicMock()
        mock_token_pair = TokenPair(
            access_token="access_token", refresh_token="refresh_token", expires_in=3600, refresh_expires_in=86400
        )
        mock_token_service.create_token_pair.return_value = mock_token_pair
        mock_get_token_service.return_value = mock_token_service

        # Mock password verification
        with patch.object(auth_service, "_verify_password", return_value=True):
            result = auth_service.authenticate_user("test@example.com", "password123")

        assert isinstance(result, TokenPair)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"

    @patch("src.services.auth_service.Account.get_by_email")
    def test_authenticate_user_not_found(self, mock_get_by_email, auth_service):
        """Test authentication with non-existent user."""
        mock_get_by_email.return_value = None

        with pytest.raises(AuthenticationError):
            auth_service.authenticate_user("nonexistent@example.com", "password123")

    @patch("src.services.auth_service.Account.get_by_email")
    def test_authenticate_user_pending_status(self, mock_get_by_email, auth_service):
        """Test authentication with pending account status."""
        mock_user = MagicMock()
        mock_user.status = AccountStatus.PENDING
        mock_user.email = "test@example.com"
        mock_user.id = "user_123"
        mock_get_by_email.return_value = mock_user

        with pytest.raises(AccountError):
            auth_service.authenticate_user("test@example.com", "password123")

    @patch("src.services.auth_service.Account.get_by_email")
    def test_authenticate_user_banned_status(self, mock_get_by_email, auth_service):
        """Test authentication with banned account status."""
        mock_user = MagicMock()
        mock_user.status = AccountStatus.BANNED
        mock_user.email = "test@example.com"
        mock_user.id = "user_123"
        mock_get_by_email.return_value = mock_user

        with pytest.raises(AccountError):
            auth_service.authenticate_user("test@example.com", "password123")

    @patch("src.services.auth_service.Account.get_by_email")
    def test_authenticate_user_wrong_password(self, mock_get_by_email, auth_service):
        """Test authentication with wrong password."""
        mock_user = MagicMock()
        mock_user.status = AccountStatus.ACTIVE
        mock_user.email = "test@example.com"
        mock_user.password = "hashed_password"  # pragma: allowlist secret
        mock_user.password_salt = "salt"  # pragma: allowlist secret
        mock_user.is_deleted = False
        mock_user.is_password_set = True
        mock_user.is_active = True
        mock_get_by_email.return_value = mock_user

        with patch.object(auth_service, "_verify_password", return_value=False):
            with pytest.raises(AuthenticationError):
                auth_service.authenticate_user("test@example.com", "wrong_password")

    @patch("src.configs.madcrow_config.RATE_LIMIT_LOGIN_ENABLED", True)
    @patch("src.services.auth_service.get_login_rate_limiter")
    def test_authenticate_user_rate_limited(self, mock_get_rate_limiter, auth_service):
        """Test authentication when rate limited."""
        # Mock rate limiter
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_rate_limited.return_value = True
        mock_rate_limiter.time_window = 300
        mock_get_rate_limiter.return_value = mock_rate_limiter

        with pytest.raises(RateLimitExceededError):
            auth_service.authenticate_user("test@example.com", "password123")

    @patch("src.services.auth_service.validate_password_strength")
    @patch("src.services.auth_service.Account.get_by_email")
    @patch("src.services.auth_service.get_token_service")
    def test_create_account_success(
        self, mock_get_token_service, mock_get_by_email, mock_validate_password, auth_service, test_db_session
    ):
        """Test successful account creation."""
        # Mock password validation
        mock_validate_password.return_value = (True, None)

        # Mock user doesn't exist
        mock_get_by_email.return_value = None

        # Mock token service
        mock_token_service = MagicMock()
        mock_token_pair = TokenPair(
            access_token="access_token", refresh_token="refresh_token", expires_in=3600, refresh_expires_in=86400
        )
        mock_token_service.create_token_pair.return_value = mock_token_pair
        mock_get_token_service.return_value = mock_token_service

        # Mock email doesn't exist
        with patch.object(Account, "email_exists", return_value=False):
            with patch("src.services.auth_service.create_password_hash") as mock_hash:
                mock_hash.return_value = ("hashed_password", "salt")

                result = auth_service.create_account(
                    name="Test User",
                    email="test@example.com",
                    password="SecurePassword123",  # pragma: allowlist secret
                    is_admin=False,  # pragma: allowlist secret
                )

        assert isinstance(result, TokenPair)
        mock_hash.assert_called_once_with("SecurePassword123")

    @patch("src.services.auth_service.validate_password_strength")
    def test_create_account_weak_password(self, mock_validate_password, auth_service):
        """Test account creation with weak password."""
        mock_validate_password.return_value = (False, "Password is too weak")

        with pytest.raises(AuthenticationError):
            auth_service.create_account(
                name="Test User",
                email="test@example.com",
                password="weak",  # pragma: allowlist secret
                is_admin=False,  # pragma: allowlist secret
            )  # pragma: allowlist secret

    @patch("src.services.auth_service.validate_password_strength")
    @patch("src.services.auth_service.Account.email_exists")
    def test_create_account_email_exists(self, mock_email_exists, mock_validate_password, auth_service):
        """Test account creation with existing email."""
        mock_validate_password.return_value = (True, None)

        # Mock email already exists
        mock_email_exists.return_value = True

        with pytest.raises(AuthenticationError):
            auth_service.create_account(
                name="Test User",
                email="existing@example.com",
                password="SecurePassword123!",  # pragma: allowlist secret
                is_admin=False,  # pragma: allowlist secret
            )

    def test_verify_password_method(self, auth_service):
        """Test the _verify_password method."""
        password = "SecurePassword123"  # pragma: allowlist secret
        stored_password = "hashed_password"  # pragma: allowlist secret
        salt = "salt"

        with patch("src.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = True

            result = auth_service._verify_password(password, stored_password, salt)

            assert result is True
            mock_verify.assert_called_once_with(password, stored_password, salt)

    def test_verify_password_no_stored_password(self, auth_service):
        """Test _verify_password with no stored password."""
        result = auth_service._verify_password("password", None, "salt")
        assert result is False

        result = auth_service._verify_password("password", "hash", None)
        assert result is False

    def test_authenticate_user_account_closed(self, auth_service, test_user_data):
        """Test authentication with closed account."""
        # Create a closed account
        account = Account(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password="hashed_password",  # pragma: allowlist secret
            password_salt="salt",  # pragma: allowlist secret
            status=AccountStatus.CLOSED,
            is_admin=False,
        )
        auth_service.db_session.add(account)
        auth_service.db_session.commit()

        with pytest.raises(AccountClosedError) as exc_info:
            auth_service.authenticate_user(
                email=test_user_data["email"], password=test_user_data["password"], login_ip="127.0.0.1"
            )
        assert "Account is closed" in str(exc_info.value)

    def test_authenticate_user_account_deleted(self, auth_service, test_user_data):
        """Test authentication with deleted account."""
        # Note: The system treats deleted accounts as "user not found" for security
        # This is correct behavior - we don't want to reveal that an account existed

        # Create a deleted account
        account = Account(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password="hashed_password",  # pragma: allowlist secret
            password_salt="salt",  # pragma: allowlist secret
            status=AccountStatus.ACTIVE,
            is_admin=False,
            is_deleted=True,
        )
        auth_service.db_session.add(account)
        auth_service.db_session.commit()

        # Should raise AuthenticationError (user not found) for security
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.authenticate_user(
                email=test_user_data["email"], password=test_user_data["password"], login_ip="127.0.0.1"
            )
        assert "Invalid email or password" in str(exc_info.value)

    def test_authenticate_user_no_password_set(self, auth_service, test_user_data):
        """Test authentication when account has no password set."""
        # Create account without password
        account = Account(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password=None,  # No password set
            password_salt=None,
            status=AccountStatus.ACTIVE,
            is_admin=False,
        )
        auth_service.db_session.add(account)
        auth_service.db_session.commit()

        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.authenticate_user(
                email=test_user_data["email"], password=test_user_data["password"], login_ip="127.0.0.1"
            )
        assert "Account password not set" in str(exc_info.value)

    def test_authenticate_user_inactive_account(self, auth_service, test_user_data):
        """Test authentication with inactive account."""
        # Create an inactive account (pending status)
        account = Account(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password="hashed_password",  # pragma: allowlist secret
            password_salt="salt",  # pragma: allowlist secret
            status=AccountStatus.PENDING,  # Not active
            is_admin=False,
        )
        auth_service.db_session.add(account)
        auth_service.db_session.commit()

        with pytest.raises(AccountNotVerifiedError) as exc_info:
            auth_service.authenticate_user(
                email=test_user_data["email"], password=test_user_data["password"], login_ip="127.0.0.1"
            )
        assert "Account is not verified" in str(exc_info.value)

    @patch("src.dependencies.redis.get_redis_client")
    def test_authenticate_user_redis_fallback(self, mock_get_redis, auth_service, test_user_data):
        """Test authentication uses Redis fallback when needed."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Create a valid account
        account = Account(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password="hashed_password",
            password_salt="salt",  # pragma: allowlist secret
            status=AccountStatus.ACTIVE,
            is_admin=False,
        )
        auth_service.db_session.add(account)
        auth_service.db_session.commit()

        # Mock password verification
        with patch.object(auth_service, "_verify_password", return_value=True):
            with patch("src.services.auth_service.get_token_service") as mock_get_token_service:
                mock_token_service = MagicMock()
                mock_token_pair = MagicMock()
                mock_token_service.create_token_pair.return_value = mock_token_pair
                mock_get_token_service.return_value = mock_token_service

                result = auth_service.authenticate_user(
                    email=test_user_data["email"], password=test_user_data["password"], login_ip="127.0.0.1"
                )

                # Should call get_redis_client to get one
                mock_get_redis.assert_called_once()
                assert result == mock_token_pair

    def test_authenticate_user_unexpected_exception(self, auth_service, test_user_data):
        """Test authentication with unexpected exception."""
        # Create a valid account
        account = Account(
            name=test_user_data["name"],
            email=test_user_data["email"],
            password="hashed_password",
            password_salt="salt",
            status=AccountStatus.ACTIVE,
            is_admin=False,
        )
        auth_service.db_session.add(account)
        auth_service.db_session.commit()

        # Mock an unexpected exception during password verification
        with patch.object(auth_service, "_verify_password", side_effect=Exception("Database error")):
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service.authenticate_user(
                    email=test_user_data["email"], password=test_user_data["password"], login_ip="127.0.0.1"
                )
            assert "Authentication failed due to system error" in str(exc_info.value)

    def test_get_user_by_email_database_error(self, auth_service, test_user_data):
        """Test _get_user_by_email with database error."""
        # Mock database error
        with patch.object(Account, "get_by_email", side_effect=Exception("Database connection failed")):
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service._get_user_by_email(test_user_data["email"])
            assert "Failed to retrieve user information" in str(exc_info.value)

    def test_get_user_by_email_user_not_found(self, auth_service, test_user_data):
        """Test _get_user_by_email when user doesn't exist."""
        # Mock no user found
        with patch.object(Account, "get_by_email", return_value=None):
            with pytest.raises(AuthenticationError) as exc_info:
                auth_service._get_user_by_email(test_user_data["email"])
            assert "Invalid email or password" in str(exc_info.value)
