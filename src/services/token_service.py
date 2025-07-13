"""JWT token service for secure authentication."""

import logging
import secrets
from datetime import datetime, timedelta
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

from ..configs import madcrow_config
from ..entities.account import Account
from ..models.token import TokenClaims, TokenPair

logger = logging.getLogger(__name__)

# Redis key prefixes for refresh tokens (following Dify pattern)
REFRESH_TOKEN_PREFIX = "refresh_token:"
ACCOUNT_REFRESH_TOKEN_PREFIX = "account_refresh_token:"


class TokenService:
    """
    JWT token service for creating and validating access and refresh tokens.

    This service provides secure JWT-based authentication with
    access and refresh token management following Dify's pattern.
    """

    # Token configuration
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days
    ALGORITHM = "HS256"

    def __init__(self, redis_client=None):
        """Initialize token service."""
        self.secret_key = madcrow_config.SECRET_KEY
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be configured for JWT tokens")
        self.redis_client = redis_client

    def create_token_pair(self, user: Account) -> TokenPair:
        """
        Create access and refresh token pair for user.

        Args:
            user: User account

        Returns:
            TokenPair: Access and refresh tokens
        """
        try:
            # Create access token
            access_token = self._create_access_token(user)

            # Create refresh token (simple random string, not JWT)
            refresh_token = self._generate_refresh_token()

            # Store refresh token in Redis following Dify pattern
            self._store_refresh_token(refresh_token, str(user.id))

            return TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_expires_in=self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )

        except Exception as e:
            logger.exception(f"Failed to create token pair for user {user.email}")
            raise RuntimeError(f"Token creation failed: {str(e)}") from e

    def _create_access_token(self, user: Account) -> str:
        """
        Create JWT access token.

        Args:
            user: User account

        Returns:
            str: JWT access token
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        claims = TokenClaims(
            sub=str(user.id),
            email=user.email,
            name=user.name,
            is_admin=user.is_admin,
            iat=int(now.timestamp()),
            exp=int(expire.timestamp()),
            jti=str(uuid4()),
            token_type="access",
        )

        return jwt.encode(claims.model_dump(), self.secret_key, algorithm=self.ALGORITHM)

    def _generate_refresh_token(self, length: int = 64) -> str:
        """
        Generate a random refresh token (following Dify pattern).

        Args:
            length: Length of the token in bytes (default: 64)

        Returns:
            str: Random hex token
        """
        return secrets.token_hex(length)

    def _get_refresh_token_key(self, refresh_token: str) -> str:
        """Get Redis key for refresh token."""
        return f"{REFRESH_TOKEN_PREFIX}{refresh_token}"

    def _get_account_refresh_token_key(self, account_id: str) -> str:
        """Get Redis key for account's current refresh token."""
        return f"{ACCOUNT_REFRESH_TOKEN_PREFIX}{account_id}"

    def _store_refresh_token(self, refresh_token: str, account_id: str) -> None:
        """
        Store refresh token in Redis (following Dify pattern).

        Args:
            refresh_token: The refresh token
            account_id: User account ID
        """
        if not self.redis_client:
            logger.warning("Redis client not available, refresh token not stored")
            return

        expiry_seconds = self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        # Store token -> account_id mapping
        self.redis_client.setex(self._get_refresh_token_key(refresh_token), expiry_seconds, account_id)

        # Store account_id -> token mapping
        self.redis_client.setex(self._get_account_refresh_token_key(account_id), expiry_seconds, refresh_token)

    def _delete_refresh_token(self, refresh_token: str, account_id: str) -> None:
        """
        Delete refresh token from Redis.

        Args:
            refresh_token: The refresh token
            account_id: User account ID
        """
        if not self.redis_client:
            return

        self.redis_client.delete(self._get_refresh_token_key(refresh_token))
        self.redis_client.delete(self._get_account_refresh_token_key(account_id))

    def verify_token(self, token: str, token_type: str = "access") -> TokenClaims | None:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            TokenClaims or None: Token claims if valid, None otherwise
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.ALGORITHM])

            # Create claims object
            claims = TokenClaims(**payload)

            # Verify token type
            if claims.token_type != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {claims.token_type}")
                return None

            # Check expiration
            if datetime.utcnow().timestamp() > claims.exp:
                logger.debug(f"Token expired: {claims.jti}")
                return None

            return claims

        except InvalidTokenError as e:
            logger.debug(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.exception("Error verifying token")
            return None

    def refresh_token_pair(self, refresh_token: str) -> TokenPair | None:
        """
        Create new token pair from refresh token (following Dify pattern).

        Args:
            refresh_token: Valid refresh token

        Returns:
            TokenPair or None: New token pair if refresh token is valid
        """
        try:
            if not self.redis_client:
                logger.error("Redis client not available for token refresh")
                return None

            # Verify the refresh token exists in Redis
            account_id_data = self.redis_client.get(self._get_refresh_token_key(refresh_token))
            if not account_id_data:
                logger.debug("Invalid or expired refresh token")
                return None

            # Handle both string and bytes return from Redis
            account_id = account_id_data.decode("utf-8") if isinstance(account_id_data, bytes) else account_id_data

            # Load user from database (you'll need to inject a way to get user)
            # For now, we'll need to modify this to accept a user lookup function
            # This is a temporary implementation
            from ..dependencies.db import get_session
            from ..services.auth_service import get_auth_service

            # This is not ideal - we should inject dependencies properly
            # But for now, this maintains the Dify pattern
            with next(get_session()) as session:
                auth_service = get_auth_service(session)
                user = auth_service.get_user_by_id(account_id)

                if not user:
                    logger.warning(f"User not found for account_id: {account_id}")
                    return None

            # Generate new tokens
            new_access_token = self._create_access_token(user)
            new_refresh_token = self._generate_refresh_token()

            # Delete old refresh token and store new one
            self._delete_refresh_token(refresh_token, account_id)
            self._store_refresh_token(new_refresh_token, account_id)

            return TokenPair(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="Bearer",
                expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_expires_in=self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )

        except Exception as e:
            logger.exception("Error refreshing token pair")
            return None

    def get_user_id_from_token(self, token: str) -> str | None:
        """
        Extract user ID from access token.

        Args:
            token: JWT access token

        Returns:
            str or None: User ID if token is valid
        """
        claims = self.verify_token(token, "access")
        return claims.sub if claims else None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without full verification.

        Args:
            token: JWT token

        Returns:
            bool: True if token is expired
        """
        try:
            # Decode without verification to check expiration
            payload = jwt.decode(token, options={"verify_signature": False})

            exp = payload.get("exp")
            if not exp:
                return True

            return datetime.utcnow().timestamp() > exp

        except Exception:
            return True

    def logout(self, account_id: str) -> None:
        """
        Logout user by deleting their refresh token (following Dify pattern).

        Args:
            account_id: User account ID
        """
        try:
            if not self.redis_client:
                return

            # Get current refresh token for the account
            refresh_token_data = self.redis_client.get(self._get_account_refresh_token_key(account_id))
            if refresh_token_data:
                # Handle both string and bytes return from Redis
                refresh_token = (
                    refresh_token_data.decode("utf-8") if isinstance(refresh_token_data, bytes) else refresh_token_data
                )
                self._delete_refresh_token(refresh_token, account_id)
                logger.info(f"Logged out user: {account_id}")

        except Exception as e:
            logger.exception(f"Error during logout for account: {account_id}")

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (placeholder for token blacklisting).

        In production, you would store revoked tokens in Redis or database.

        Args:
            token: Token to revoke

        Returns:
            bool: True if token was revoked successfully
        """
        try:
            claims = self.verify_token(token)
            if not claims:
                return False

            # TODO: Implement token blacklisting in Redis
            # redis_client.set(f"revoked_token:{claims.jti}", "1", ex=claims.exp - int(datetime.utcnow().timestamp()))

            logger.info(f"Token revoked: {claims.jti}")
            return True

        except Exception as e:
            logger.exception("Error revoking token")
            return False


# Global token service instance
token_service = None


def get_token_service(redis_client=None) -> TokenService:
    """
    Get token service instance.

    Args:
        redis_client: Redis client instance (optional)

    Returns:
        TokenService: Token service instance
    """
    global token_service
    if token_service is None:
        token_service = TokenService(redis_client)
    elif redis_client and not token_service.redis_client:
        token_service.redis_client = redis_client
    return token_service
