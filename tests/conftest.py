"""Pytest configuration and shared fixtures for all tests."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from app import create_app
from src.configs import madcrow_config
from src.entities.account import Account
from src.entities.status import AccountStatus
from src.services.auth_service import AuthService
from src.utils.rate_limiter import RateLimiter


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url():
    """Create a temporary SQLite database for testing."""
    # Use in-memory SQLite for faster tests
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Create a test database engine using SQLModel."""
    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables using SQLModel
    SQLModel.metadata.create_all(bind=engine)
    yield engine

    # Cleanup
    SQLModel.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_engine):
    """Create a test database session using SQLModel Session with table cleanup."""
    session = Session(test_engine)

    try:
        yield session
    finally:
        # Clean up all data from tables instead of rolling back transactions
        # This allows data to persist within a single test but cleans up between tests
        try:
            # Delete all records from all tables
            for table in reversed(SQLModel.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


@pytest.fixture
def mock_redis():
    """Create a comprehensive mock Redis client for testing."""
    mock_redis_client = MagicMock(spec=redis.Redis)

    # Internal storage for testing
    mock_storage = {}
    mock_sorted_sets = {}

    def mock_get(key):
        return mock_storage.get(key)

    def mock_set(key, value, ex=None, px=None, nx=False, xx=False):
        if nx and key in mock_storage:
            return False
        if xx and key not in mock_storage:
            return False
        mock_storage[key] = value
        return True

    def mock_setex(key, time, value):
        mock_storage[key] = value
        return True

    def mock_delete(*keys):
        count = 0
        for key in keys:
            deleted = False
            if key in mock_storage:
                del mock_storage[key]
                deleted = True
            if key in mock_sorted_sets:
                del mock_sorted_sets[key]
                deleted = True
            if deleted:
                count += 1
        return count

    def mock_exists(key):
        return key in mock_storage

    def mock_expire(key, time):
        return key in mock_storage

    def mock_zadd(name, mapping, nx=False, xx=False, ch=False, incr=False):
        if name not in mock_sorted_sets:
            mock_sorted_sets[name] = {}
        mock_sorted_sets[name].update(mapping)
        return len(mapping)

    def mock_zcard(name):
        return len(mock_sorted_sets.get(name, {}))

    def mock_zremrangebyscore(name, min_score, max_score):
        if name not in mock_sorted_sets:
            return 0

        # Handle special Redis values
        if min_score == "-inf":
            min_score = float("-inf")
        elif isinstance(min_score, str):
            min_score = float(min_score)

        if max_score == "+inf":
            max_score = float("inf")
        elif isinstance(max_score, str):
            max_score = float(max_score)

        to_remove = [k for k, v in mock_sorted_sets[name].items() if min_score <= float(v) <= max_score]
        for key in to_remove:
            del mock_sorted_sets[name][key]
        return len(to_remove)

    def mock_zcount(name, min_score, max_score):
        if name not in mock_sorted_sets:
            return 0

        # Handle special Redis values
        if min_score == "-inf":
            min_score = float("-inf")
        elif isinstance(min_score, str):
            min_score = float(min_score)

        if max_score == "+inf":
            max_score = float("inf")
        elif isinstance(max_score, str):
            max_score = float(max_score)

        return len([k for k, v in mock_sorted_sets[name].items() if min_score <= float(v) <= max_score])

    def mock_zrange(name, start, end, withscores=False):
        if name not in mock_sorted_sets:
            return []

        # Get sorted items by score
        items = sorted(mock_sorted_sets[name].items(), key=lambda x: float(x[1]))

        # Handle negative indices
        if start < 0:
            start = len(items) + start
        if end < 0:
            end = len(items) + end

        # Slice the items
        sliced_items = items[start : end + 1] if end >= 0 else items[start:]

        if withscores:
            return [(item[0], float(item[1])) for item in sliced_items]
        else:
            return [item[0] for item in sliced_items]

    # Assign mock functions
    mock_redis_client.get.side_effect = mock_get
    mock_redis_client.set.side_effect = mock_set
    mock_redis_client.setex.side_effect = mock_setex
    mock_redis_client.delete.side_effect = mock_delete
    mock_redis_client.exists.side_effect = mock_exists
    mock_redis_client.expire.side_effect = mock_expire
    mock_redis_client.zadd.side_effect = mock_zadd
    mock_redis_client.zcard.side_effect = mock_zcard
    mock_redis_client.zremrangebyscore.side_effect = mock_zremrangebyscore
    mock_redis_client.zcount.side_effect = mock_zcount
    mock_redis_client.zrange.side_effect = mock_zrange

    # Add storage access for testing
    mock_redis_client._storage = mock_storage
    mock_redis_client._sorted_sets = mock_sorted_sets

    return mock_redis_client


@pytest.fixture
def rate_limiter(mock_redis):
    """Create a RateLimiter instance for testing."""
    return RateLimiter(redis_client=mock_redis)


@pytest.fixture
def auth_service(test_db_session, mock_redis):
    """Create an AuthService instance for testing with mocked dependencies."""
    with patch("src.dependencies.redis.get_redis_client") as mock_get_redis:
        with patch("src.extensions.ext_redis.is_redis_available") as mock_redis_available:
            with patch("src.configs.madcrow_config.RATE_LIMIT_LOGIN_ENABLED", True):
                mock_get_redis.return_value = mock_redis
                mock_redis_available.return_value = True
                service = AuthService(db_session=test_db_session)
                yield service


@pytest.fixture
def test_app(test_db_session, mock_redis):
    """Create a test FastAPI application with mocked dependencies."""
    # Create a mock Redis client that appears initialized
    mock_redis_client = MagicMock()
    mock_redis_client.get_client.return_value = mock_redis
    mock_redis_client.is_initialized.return_value = True
    mock_redis_client._is_initialized = True
    mock_redis_client._client = mock_redis

    # Create a generator function for get_session
    def mock_get_session_generator():
        yield test_db_session

    with patch("src.dependencies.db.get_session", mock_get_session_generator) as mock_get_db:
        with patch("src.dependencies.redis.get_redis_client") as mock_get_redis:
            with patch("src.dependencies.redis.is_redis_available") as mock_redis_available_dep:
                with patch("src.extensions.ext_redis.get_redis") as mock_ext_redis:
                    with patch("src.extensions.ext_redis.is_redis_available") as mock_redis_available:
                        with patch("src.extensions.ext_redis.redis_client", mock_redis_client):
                            with patch("src.configs.madcrow_config.LOGIN_DISABLED", True):
                                with patch("src.extensions.ext_db.init_app") as mock_db_init:
                                    with patch("src.extensions.ext_redis.init_app") as mock_redis_init:
                                        with patch("src.extensions.ext_db.db_engine.get_engine") as mock_engine:
                                            with patch("src.configs.madcrow_config.DEPLOY_ENV", "DEVELOPMENT"):
                                                with patch(
                                                    "src.configs.madcrow_config.DB_CONNECTION_TEST_ON_STARTUP", False
                                                ):
                                                    with patch(
                                                        "src.configs.madcrow_config.SECRET_KEY",
                                                        "test-secret-key-for-testing-only",
                                                    ):
                                                        # Mock all database dependency functions
                                                        # mock_get_db is now a generator function
                                                        mock_engine.return_value = test_db_session.bind

                                                        # Mock all Redis dependency functions
                                                        mock_get_redis.return_value = mock_redis
                                                        mock_ext_redis.return_value = mock_redis
                                                        mock_redis_available.return_value = True
                                                        mock_redis_available_dep.return_value = True

                                                        # Mock extension initialization
                                                        mock_db_init.return_value = None
                                                        mock_redis_init.return_value = None

                                                        app = create_app()
                                                        yield app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI application."""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def test_user_data():
    """Sample user data for testing with unique identifiers."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": f"Test User {unique_id}",
        "email": f"test-{unique_id}@example.com",
        "password": "SecurePassword123",  # pragma: allowlist secret
        "is_admin": False,
    }


@pytest.fixture
def test_admin_data():
    """Sample admin user data for testing with unique identifiers."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": f"Admin User {unique_id}",
        "email": f"admin-{unique_id}@example.com",
        "password": "AdminPassword123",  # pragma: allowlist secret
        "is_admin": True,
    }


@pytest.fixture
def unique_user_factory():
    """Factory to create unique user data for each test."""

    def _create_user(prefix="user", is_admin=False, **kwargs):
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        base_data = {
            "name": f"{prefix.title()} {unique_id}",
            "email": f"{prefix}-{unique_id}@example.com",
            "password": "SecurePassword123",  # pragma: allowlist secret
            "is_admin": is_admin,
        }
        base_data.update(kwargs)
        return base_data

    return _create_user


@pytest.fixture
def test_account_data():
    """Sample account data with proper status for testing."""
    return {
        "name": "Test Account",
        "email": "account@example.com",
        "password": "TestPassword123",  # pragma: allowlist secret
        "status": AccountStatus.ACTIVE,
    }


@pytest.fixture(autouse=True)
def reset_token_service():
    """Reset the global token service between tests."""
    import src.services.token_service as ts

    ts.token_service = None
    yield
    ts.token_service = None


@pytest.fixture
def created_test_user(test_db_session, test_user_data, mock_redis):
    """Create a test user in the database with token pair and working refresh functionality."""
    from src.libs.password import create_password_hash
    from src.services.token_service import TokenService, get_token_service

    # Create password hash
    password_hash, salt = create_password_hash(test_user_data["password"])

    # Create account
    account = Account(
        name=test_user_data["name"],
        email=test_user_data["email"],
        password=password_hash,  # Use 'password' not 'password_hash'
        password_salt=salt,  # Use 'password_salt' not 'salt'
        status=AccountStatus.ACTIVE,
        is_admin=test_user_data.get("is_admin", False),
    )

    test_db_session.add(account)
    test_db_session.commit()
    test_db_session.refresh(account)

    # Create token pair for the user using TokenService
    with patch("src.configs.madcrow_config.SECRET_KEY", "test-secret-key-for-testing-only"):
        token_service = get_token_service(mock_redis)
        token_pair = token_service.create_token_pair(account)

        # Mock the refresh_token_pair method to work properly in tests
        def mock_refresh_token_pair(refresh_token: str):
            # Check if the refresh token exists in our mock storage
            token_key = f"refresh_token:{refresh_token}"
            if token_key in mock_redis._storage:
                # Create new tokens
                new_access_token = token_service._create_access_token(account)
                new_refresh_token = token_service._generate_refresh_token()

                # Update storage
                mock_redis._storage[f"refresh_token:{new_refresh_token}"] = str(account.id)
                mock_redis._storage[f"account_refresh_token:{account.id}"] = new_refresh_token

                # Remove old token
                del mock_redis._storage[token_key]
                if f"account_refresh_token:{account.id}" in mock_redis._storage:
                    del mock_redis._storage[f"account_refresh_token:{account.id}"]

                from src.models.token import TokenPair

                return TokenPair(
                    access_token=new_access_token,
                    refresh_token=new_refresh_token,
                    token_type="Bearer",
                    expires_in=TokenService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    refresh_expires_in=TokenService.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                )
            return None

        # Patch the refresh method globally for this test
        with patch.object(token_service, "refresh_token_pair", mock_refresh_token_pair):
            # Also patch the global token service to use our mocked version
            import src.services.token_service as ts

            ts.token_service = token_service

            # Return a dictionary that includes both user data and token info
            # This maintains backward compatibility with tests expecting direct access to user fields
            result = {
                "user": account,
                "token_pair": token_pair,
                # Add direct access to user fields for backward compatibility
                "id": account.id,
                "name": account.name,
                "email": account.email,
                "password": test_user_data["password"],  # Original password for login tests
                "is_admin": account.is_admin,
                "status": account.status,
                "access_token": token_pair.access_token,
                "refresh_token": token_pair.refresh_token,
            }
            yield result


@pytest.fixture
def created_test_admin(test_db_session, test_admin_data):
    """Create a test admin user in the database."""
    from src.libs.password import create_password_hash

    # Create password hash
    password_hash, salt = create_password_hash(test_admin_data["password"])

    # Create account
    account = Account(
        name=test_admin_data["name"],
        email=test_admin_data["email"],
        password=password_hash,
        password_salt=salt,
        status=AccountStatus.ACTIVE,
        is_admin=test_admin_data.get("is_admin", True),
    )

    test_db_session.add(account)
    test_db_session.commit()
    test_db_session.refresh(account)

    return account


@pytest.fixture
def jwt_token_data():
    """Sample JWT token data for testing."""
    return {
        "sub": "test@example.com",
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "exp": 1234567890,
        "iat": 1234567890,
        "type": "access",
    }


@pytest.fixture
def mock_jwt_service():
    """Create a mock JWT service for testing."""
    mock_service = MagicMock()
    mock_service.create_access_token.return_value = "mock_access_token"
    mock_service.create_refresh_token.return_value = "mock_refresh_token"
    mock_service.verify_token.return_value = {
        "sub": "test@example.com",
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "type": "access",
    }
    return mock_service


@pytest.fixture
def valid_login_data(test_user_data):
    """Valid login request data that matches the created test user."""
    return {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
        "remember_me": False,
    }


@pytest.fixture
def invalid_login_data():
    """Invalid login request data."""
    return {
        "email": "nonexistent@example.com",
        "password": "wrongpassword",  # pragma: allowlist secret
        "remember_me": False,
    }


@pytest.fixture
def valid_register_data():
    """Valid registration request data."""
    return {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "NewPassword123",  # pragma: allowlist secret
    }


@pytest.fixture
def weak_password_register_data():
    """Registration data with weak password."""
    return {
        "name": "Weak User",
        "email": "weak@example.com",
        "password": "123",
    }


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch.object(madcrow_config, "RATE_LIMITING_ENABLED", True):
        with patch.object(madcrow_config, "LOGIN_RATE_LIMIT_MAX_ATTEMPTS", 5):
            with patch.object(madcrow_config, "LOGIN_RATE_LIMIT_TIME_WINDOW", 300):
                yield madcrow_config


# Add __init__.py files for test subdirectories
@pytest.fixture(scope="session", autouse=True)
def create_test_init_files():
    """Create __init__.py files in test subdirectories."""
    import os
    from pathlib import Path

    # Get the current working directory and adjust paths accordingly
    current_dir = os.getcwd()

    test_dirs = ["unit", "integration", "api", "e2e", "performance", "security"]
    for test_dir in test_dirs:
        # Handle different execution contexts
        if current_dir.endswith("/tests"):
            # Running from tests directory
            init_file = f"{test_dir}/__init__.py"
            dir_path = test_dir
        else:
            # Running from project root
            init_file = f"tests/{test_dir}/__init__.py"
            dir_path = f"tests/{test_dir}"

        # Create directory if it doesn't exist
        Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Create __init__.py file if it doesn't exist
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""Test package for {test_dir} tests."""\n')
