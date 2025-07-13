"""Session management service using Redis for storing user sessions."""

import json
import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from ..dependencies.redis import RedisService
from ..entities.account import Account
from ..models.auth import SessionInfo, UserProfile

logger = logging.getLogger(__name__)


class SessionService:
    """
    Session management service using Redis for session storage.

    This service handles user session creation, validation, and cleanup
    with secure session management and expiration handling.
    """

    # Session configuration
    DEFAULT_SESSION_DURATION = 24 * 60 * 60  # 24 hours in seconds
    REMEMBER_ME_DURATION = 30 * 24 * 60 * 60  # 30 days in seconds
    SESSION_KEY_PREFIX = "session:"
    USER_SESSIONS_PREFIX = "user_sessions:"

    def __init__(self, redis_service: RedisService):
        """
        Initialize session service.

        Args:
            redis_service: Redis service for session storage
        """
        self.redis = redis_service

    def create_session(self, user: Account, remember_me: bool = False, login_ip: str | None = None) -> SessionInfo:
        """
        Create a new user session.

        Args:
            user: User account
            remember_me: Whether to create extended session
            login_ip: IP address of the login

        Returns:
            SessionInfo: Created session information
        """
        try:
            # Generate session ID
            session_id = f"sess_{uuid4().hex}"

            # Calculate expiration
            duration = self.REMEMBER_ME_DURATION if remember_me else self.DEFAULT_SESSION_DURATION
            expires_at = datetime.utcnow() + timedelta(seconds=duration)

            # Create session data
            session_data = {
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name,
                "is_admin": user.is_admin,
                "status": user.status.value,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
                "remember_me": remember_me,
                "login_ip": login_ip,
                "last_activity": datetime.utcnow().isoformat(),
            }

            # Store session in Redis
            success = self.redis.set_session(session_id, session_data, duration)

            if not success:
                raise RuntimeError("Failed to store session in Redis")

            # Track user sessions (for logout all functionality)
            self._add_user_session(user.id, session_id, duration)

            logger.info(f"Created session for user {user.email}: {session_id}")

            return SessionInfo(session_id=session_id, expires_at=expires_at, remember_me=remember_me)

        except Exception as e:
            logger.exception(f"Failed to create session for user {user.email}")
            raise RuntimeError(f"Session creation failed: {str(e)}") from e

    def validate_session(self, session_id: str) -> dict | None:
        """
        Validate and retrieve session data.

        Args:
            session_id: Session identifier

        Returns:
            dict or None: Session data if valid, None otherwise
        """
        if not session_id:
            return None

        try:
            # Get session data from Redis
            session_data = self.redis.get_session(session_id)

            if not session_data:
                logger.debug(f"Session not found: {session_id}")
                return None

            # Check expiration
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.debug(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None

            # Update last activity
            session_data["last_activity"] = datetime.utcnow().isoformat()

            # Extend session if it's a remember_me session
            if session_data.get("remember_me", False):
                self._extend_session(session_id, session_data)

            logger.debug(f"Session validated: {session_id}")
            return session_data

        except Exception:
            logger.exception(f"Error validating session: {session_id}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a user session.

        Args:
            session_id: Session identifier

        Returns:
            bool: True if session was deleted, False otherwise
        """
        try:
            # Get session data to find user ID
            session_data = self.redis.get_session(session_id)

            # Delete session
            deleted = self.redis.delete_session(session_id)

            # Remove from user sessions tracking
            if session_data and "user_id" in session_data:
                self._remove_user_session(UUID(session_data["user_id"]), session_id)

            if deleted:
                logger.info(f"Deleted session: {session_id}")

            return deleted

        except Exception:
            logger.exception(f"Error deleting session: {session_id}")
            return False

    def delete_all_user_sessions(self, user_id: UUID) -> int:
        """
        Delete all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            int: Number of sessions deleted
        """
        try:
            # Get all user sessions
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
            sessions_data = self.redis.get_cache(user_sessions_key)

            if not sessions_data:
                return 0

            session_ids = json.loads(sessions_data)
            deleted_count = 0

            # Delete each session
            for session_id in session_ids:
                if self.redis.delete_session(session_id):
                    deleted_count += 1

            # Clear user sessions tracking
            self.redis.delete_cache(user_sessions_key)

            logger.info(f"Deleted {deleted_count} sessions for user: {user_id}")
            return deleted_count

        except Exception:
            logger.exception(f"Error deleting all sessions for user: {user_id}")
            return 0

    def get_user_from_session(self, session_id: str) -> UserProfile | None:
        """
        Get user profile from session.

        Args:
            session_id: Session identifier

        Returns:
            UserProfile or None: User profile if session is valid
        """
        session_data = self.validate_session(session_id)

        if not session_data:
            return None

        try:
            return UserProfile(
                id=UUID(session_data["user_id"]),
                name=session_data["name"],
                email=session_data["email"],
                status=session_data["status"],
                timezone=session_data.get("timezone"),
                avatar=session_data.get("avatar"),
                is_admin=session_data["is_admin"],
                last_login_at=datetime.fromisoformat(session_data["created_at"]),
                initialized_at=None,  # Not stored in session
                created_at=datetime.fromisoformat(session_data["created_at"]),
            )

        except Exception:
            logger.exception(f"Error creating user profile from session: {session_id}")
            return None

    def _extend_session(self, session_id: str, session_data: dict) -> None:
        """
        Extend session expiration for remember_me sessions.

        Args:
            session_id: Session identifier
            session_data: Current session data
        """
        try:
            # Extend expiration by remember_me duration
            new_expires_at = datetime.utcnow() + timedelta(seconds=self.REMEMBER_ME_DURATION)
            session_data["expires_at"] = new_expires_at.isoformat()

            # Update session in Redis
            self.redis.set_session(session_id, session_data, self.REMEMBER_ME_DURATION)

            logger.debug(f"Extended session: {session_id}")

        except Exception:
            logger.exception(f"Error extending session: {session_id}")

    def _add_user_session(self, user_id: UUID, session_id: str, duration: int) -> None:
        """
        Track session for a user.

        Args:
            user_id: User ID
            session_id: Session identifier
            duration: Session duration in seconds
        """
        try:
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"

            # Get existing sessions
            sessions_data = self.redis.get_cache(user_sessions_key)
            session_ids = json.loads(sessions_data) if sessions_data else []

            # Add new session
            if session_id not in session_ids:
                session_ids.append(session_id)

            # Store updated list
            self.redis.set_cache(user_sessions_key, json.dumps(session_ids), duration)

        except Exception:
            logger.exception(f"Error tracking user session: {user_id}, {session_id}")

    def _remove_user_session(self, user_id: UUID, session_id: str) -> None:
        """
        Remove session from user tracking.

        Args:
            user_id: User ID
            session_id: Session identifier
        """
        try:
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"

            # Get existing sessions
            sessions_data = self.redis.get_cache(user_sessions_key)
            if not sessions_data:
                return

            session_ids = json.loads(sessions_data)

            # Remove session
            if session_id in session_ids:
                session_ids.remove(session_id)

                if session_ids:
                    # Update list
                    self.redis.set_cache(user_sessions_key, json.dumps(session_ids), self.REMEMBER_ME_DURATION)
                else:
                    # Delete empty list
                    self.redis.delete_cache(user_sessions_key)

        except Exception:
            logger.exception(f"Error removing user session: {user_id}, {session_id}")


def get_session_service(redis_service: RedisService) -> SessionService:
    """
    Factory function to create SessionService instance.

    Args:
        redis_service: Redis service

    Returns:
        SessionService: Configured session service
    """
    return SessionService(redis_service)
