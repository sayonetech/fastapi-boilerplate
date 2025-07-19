"""Unit tests for TokenService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import jwt
import pytest

from src.entities.account import Account, AccountStatus
from src.models.token import TokenClaims, TokenPair
from src.services.token_service import TokenService, get_token_service


@pytest.mark.unit
class TestTokenService:
    """Test TokenService functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client."""
        return Mock()

    @pytest.fixture
    def token_service(self, mock_redis_client):
        """Create TokenService instance with mocked Redis."""
        with patch("src.services.token_service.madcrow_config") as mock_config:
            mock_config.SECRET_KEY = "test_secret_key_for_jwt_tokens"  # pragma: allowlist secret
            return TokenService(mock_redis_client)

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
            initialized_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_init_with_secret_key(self, mock_redis_client):
        """Test TokenService initialization with valid secret key."""
        with patch("src.services.token_service.madcrow_config") as mock_config:
            mock_config.SECRET_KEY = "test_secret_key"  # pragma: allowlist secret
            service = TokenService(mock_redis_client)

            assert service.secret_key == "test_secret_key"  # pragma: allowlist secret
            assert service.redis_client == mock_redis_client

    def test_init_without_secret_key(self, mock_redis_client):
        """Test TokenService initialization without secret key."""
        with patch("src.services.token_service.madcrow_config") as mock_config:
            mock_config.SECRET_KEY = None

            with pytest.raises(ValueError, match="SECRET_KEY must be configured"):
                TokenService(mock_redis_client)

    def test_init_empty_secret_key(self, mock_redis_client):
        """Test TokenService initialization with empty secret key."""
        with patch("src.services.token_service.madcrow_config") as mock_config:
            mock_config.SECRET_KEY = ""

            with pytest.raises(ValueError, match="SECRET_KEY must be configured"):
                TokenService(mock_redis_client)

    def test_create_token_pair_success(self, token_service, sample_user):
        """Test successful token pair creation."""
        token_service.redis_client.setex.return_value = True

        result = token_service.create_token_pair(sample_user)

        assert isinstance(result, TokenPair)
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "Bearer"  # Fixed: actual value is "Bearer"
        assert result.expires_in == token_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # Verify refresh token was stored in Redis
        token_service.redis_client.setex.assert_called()

    def test_create_access_token(self, token_service, sample_user):
        """Test access token creation."""
        token = token_service._create_access_token(sample_user)  # Fixed: method is private

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify token
        decoded = jwt.decode(token, token_service.secret_key, algorithms=[token_service.ALGORITHM])
        assert decoded["sub"] == str(sample_user.id)
        assert decoded["email"] == sample_user.email
        assert decoded["name"] == sample_user.name
        assert decoded["is_admin"] == sample_user.is_admin
        assert "exp" in decoded
        assert "iat" in decoded

    def test_verify_token_valid(self, token_service, sample_user):
        """Test verification of valid access token."""
        token = token_service._create_access_token(sample_user)

        result = token_service.verify_token(token, "access")

        assert result is not None
        assert isinstance(result, TokenClaims)
        assert result.sub == str(sample_user.id)
        assert result.email == sample_user.email
        assert result.name == sample_user.name
        assert result.is_admin == sample_user.is_admin

    def test_verify_token_invalid(self, token_service):
        """Test verification of invalid access token."""
        result = token_service.verify_token("invalid_token", "access")
        assert result is None

    def test_verify_token_expired(self, token_service, sample_user):
        """Test verification of expired access token."""
        # Create token with past expiration
        past_time = datetime.now(UTC) - timedelta(hours=2)
        payload = {
            "sub": str(sample_user.id),
            "email": sample_user.email,
            "name": sample_user.name,
            "is_admin": sample_user.is_admin,
            "exp": past_time,
            "iat": past_time - timedelta(hours=1),
            "token_type": "access",
        }
        expired_token = jwt.encode(payload, token_service.secret_key, algorithm=token_service.ALGORITHM)

        result = token_service.verify_token(expired_token, "access")
        assert result is None

    def test_verify_token_wrong_secret(self, token_service, sample_user):
        """Test verification of token with wrong secret."""
        # Create token with different secret
        wrong_secret = "wrong_secret_key"  # pragma: allowlist secret
        payload = {
            "sub": str(sample_user.id),
            "email": sample_user.email,
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "token_type": "access",
        }
        wrong_token = jwt.encode(payload, wrong_secret, algorithm=token_service.ALGORITHM)

        result = token_service.verify_token(wrong_token, "access")
        assert result is None

    def test_refresh_token_pair_success(self, token_service, sample_user):
        """Test successful token pair refresh."""
        # Create initial token pair
        token_service.redis_client.setex.return_value = True
        initial_pair = token_service.create_token_pair(sample_user)

        # Mock Redis to return user ID for refresh token
        token_service.redis_client.get.return_value = str(sample_user.id).encode()

        # Mock database session and user retrieval
        with (
            patch("src.dependencies.db.get_session") as mock_get_session,
            patch("src.services.auth_service.get_auth_service") as mock_get_auth_service,
        ):
            # Mock session context manager properly
            mock_session = Mock()
            mock_session.__enter__ = Mock(return_value=mock_session)
            mock_session.__exit__ = Mock(return_value=None)
            mock_get_session.return_value = iter([mock_session])

            # Mock auth service and user retrieval
            mock_auth_service = Mock()
            mock_auth_service.get_user_by_id.return_value = sample_user
            mock_get_auth_service.return_value = mock_auth_service

            result = token_service.refresh_token_pair(initial_pair.refresh_token)

        assert result is not None
        assert isinstance(result, TokenPair)
        assert result.access_token is not None
        assert result.refresh_token is not None

    def test_refresh_token_pair_invalid_token(self, token_service):
        """Test token pair refresh with invalid refresh token."""
        token_service.redis_client.get.return_value = None

        result = token_service.refresh_token_pair("invalid_token")
        assert result is None

    def test_get_user_id_from_token_valid(self, token_service, sample_user):
        """Test getting user ID from valid token."""
        token = token_service._create_access_token(sample_user)

        result = token_service.get_user_id_from_token(token)

        assert result == str(sample_user.id)

    def test_get_user_id_from_token_invalid(self, token_service):
        """Test getting user ID from invalid token."""
        result = token_service.get_user_id_from_token("invalid_token")
        assert result is None

    def test_is_token_expired_not_expired(self, token_service, sample_user):
        """Test checking if token is expired - not expired."""
        token = token_service._create_access_token(sample_user)

        result = token_service.is_token_expired(token)
        assert result is False

    def test_is_token_expired_expired(self, token_service, sample_user):
        """Test checking if token is expired - expired."""
        # Create expired token
        past_time = datetime.now(UTC) - timedelta(hours=2)
        payload = {"sub": str(sample_user.id), "exp": past_time}
        expired_token = jwt.encode(payload, token_service.secret_key, algorithm=token_service.ALGORITHM)

        result = token_service.is_token_expired(expired_token)
        assert result is True

    def test_is_token_expired_invalid_token(self, token_service):
        """Test checking if invalid token is expired."""
        result = token_service.is_token_expired("invalid_token")
        assert result is True

    def test_logout_success(self, token_service):
        """Test successful user logout."""
        user_id = str(uuid4())
        token_service.redis_client.get.return_value = b"refresh_token_123"
        token_service.redis_client.delete.return_value = 1

        # Should not raise exception
        token_service.logout(user_id)

        # Verify Redis calls were made
        token_service.redis_client.get.assert_called()
        token_service.redis_client.delete.assert_called()

    def test_logout_no_token(self, token_service):
        """Test logout when user has no refresh token."""
        user_id = str(uuid4())
        token_service.redis_client.get.return_value = None

        # Should not raise exception
        token_service.logout(user_id)

    def test_revoke_token_placeholder(self, token_service):
        """Test token revocation placeholder."""
        result = token_service.revoke_token("some_token")

        # This is a placeholder method, so it should return False
        assert result is False


@pytest.mark.unit
def test_get_token_service():
    """Test token service factory function."""
    mock_redis = Mock()

    with patch("src.services.token_service.madcrow_config") as mock_config:
        mock_config.SECRET_KEY = "test_secret"  # pragma: allowlist secret
        service = get_token_service(mock_redis)

        assert isinstance(service, TokenService)
        assert service.redis_client == mock_redis
