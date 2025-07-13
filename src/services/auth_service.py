"""Authentication service for user login and session management."""

import logging

# datetime imports moved to Account model
from uuid import UUID

from sqlmodel import Session, select

from ..entities.account import Account
from ..entities.status import AccountStatus
from ..exceptions import (
    AccountBannedError,
    AccountClosedError,
    AccountError,
    AccountLoginError,
    AccountNotVerifiedError,
    AuthenticationError,
)
from ..libs.password import (
    create_password_hash,
    validate_password_strength,
    verify_password,
)
from ..models.token import TokenPair
from ..services.token_service import get_token_service
from ..utils.error_factory import ErrorFactory

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service providing login functionality.

    This service handles user authentication, password verification,
    and JWT token management with secure password hashing.
    """

    def __init__(self, db_session: Session):
        """
        Initialize authentication service.

        Args:
            db_session: Database session for user operations
        """
        self.db_session = db_session

    def authenticate_user(self, email: str, password: str, login_ip: str | None = None) -> TokenPair:
        """
        Authenticate user with email and password.

        Args:
            email: User email address
            password: Plain text password
            login_ip: IP address of the login attempt

        Returns:
            TokenPair: Access and refresh tokens for authenticated user

        Raises:
            AuthenticationError: If authentication fails
            AccountError: If account is not in valid state
        """
        # Note: Basic validation is handled by LoginRequest model

        try:
            # Find user by email using Account model method
            user = Account.get_by_email(self.db_session, email.strip().lower())
            if not user:
                logger.warning(f"User not found for email: {email}")
                raise ErrorFactory.create_authentication_error(
                    message="Invalid email or password", context={"reason": "user_not_found"}
                )

            # Check account status first (following Dify pattern)
            if user.status == AccountStatus.PENDING:
                raise AccountNotVerifiedError(email=email, account_id=user.id)

            if user.status == AccountStatus.BANNED:
                raise AccountBannedError("Account is banned.", email=email, account_id=user.id)

            if user.status == AccountStatus.CLOSED:
                raise AccountClosedError("Account is closed.", email=email, account_id=user.id)

            # Check if account is deleted
            if user.is_deleted:
                raise AccountLoginError("Account has been deleted.", email=email, account_id=user.id)

            # Check if password is set
            if not user.is_password_set:
                raise ErrorFactory.create_authentication_error(
                    message="Account password not set", context={"reason": "no_password"}
                )

            # Final check - account must be active to login
            if not user.is_active:
                raise AccountLoginError(
                    f"Account status is {user.status.value} and cannot login.", email=email, account_id=user.id
                )

            # Verify password
            if not self._verify_password(password, user.password, user.password_salt):
                logger.warning(f"Failed login attempt for email: {email}")
                raise ErrorFactory.create_authentication_error(
                    message="Invalid email or password", context={"reason": "invalid_credentials"}
                )

            # Update last login information using Account model method
            user.update_last_login(login_ip)
            self.db_session.commit()

            # Create token pair with Redis support
            from ..dependencies.redis import get_redis_client

            redis_client = get_redis_client()
            token_service = get_token_service(redis_client)
            token_pair = token_service.create_token_pair(user)

            logger.info(f"Successful login for user: {user.email}")
            return token_pair

        except (
            AuthenticationError,
            AccountError,
            AccountNotVerifiedError,
            AccountBannedError,
            AccountClosedError,
            AccountLoginError,
        ):
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during authentication for email: {email}")
            raise ErrorFactory.create_authentication_error(
                message="Authentication failed due to system error",
                context={"error_type": type(e).__name__, "error_message": str(e)},
            )

    def _get_user_by_email(self, email: str) -> Account:
        """
        Get user account by email address.

        Args:
            email: User email address

        Returns:
            Account: User account

        Raises:
            AuthenticationError: If user not found
        """
        try:
            statement = select(Account).where(Account.email == email, Account.is_deleted is False)
            user = self.db_session.exec(statement).first()

            if not user:
                logger.warning(f"User not found for email: {email}")
                raise ErrorFactory.create_authentication_error(
                    message="Invalid email or password", context={"reason": "user_not_found"}
                )

            return user

        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.exception(f"Database error while fetching user: {email}")
            raise ErrorFactory.create_authentication_error(
                message="Failed to retrieve user information",
                context={"error_type": type(e).__name__, "error_message": str(e)},
            )

    def _verify_password(self, password: str, stored_password: str | None, salt: str | None) -> bool:
        """
        Verify password against stored password and salt.

        Args:
            password: Plain text password
            stored_password: Stored hashed password
            salt: Password salt

        Returns:
            bool: True if password is valid, False otherwise
        """
        if not stored_password or not salt:
            logger.warning("User has no password or salt set")
            return False

        try:
            return verify_password(password, stored_password, salt)
        except Exception:
            logger.exception("Error verifying password")
            return False

    def create_account(self, name: str, email: str, password: str, is_admin: bool = False) -> TokenPair:
        """
        Create new user account with secure password handling.

        Args:
            name: User full name
            email: User email address
            password: Plain text password
            is_admin: Whether user should have admin privileges

        Returns:
            TokenPair: Access and refresh tokens for new user

        Raises:
            AuthenticationError: If account creation fails
            AccountError: If account validation fails
        """
        # Note: Basic field validation is handled by RegisterRequest model

        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            raise ErrorFactory.create_authentication_error(
                message=error_message, context={"field": "password", "reason": "weak"}
            )

        try:
            # Check if email already exists using Account model method
            if Account.email_exists(self.db_session, email.strip().lower()):
                raise ErrorFactory.create_authentication_error(
                    message="Email address is already registered", context={"field": "email", "reason": "duplicate"}
                )

            # Create password hash and salt
            hashed_password, password_salt = create_password_hash(password)

            # Create new account
            new_account = Account(
                name=name.strip(),
                email=email.strip().lower(),
                password=hashed_password,
                password_salt=password_salt,
                status=AccountStatus.ACTIVE,  # Auto-activate for now
                is_admin=is_admin,
                timezone="UTC",
            )

            # Activate the account using Account model method
            new_account.activate()

            # Save to database
            self.db_session.add(new_account)
            self.db_session.commit()
            self.db_session.refresh(new_account)

            # Create token pair with Redis support
            from ..dependencies.redis import get_redis_client

            redis_client = get_redis_client()
            token_service = get_token_service(redis_client)
            token_pair = token_service.create_token_pair(new_account)

            logger.info(f"Created new account for user: {new_account.email}")
            return token_pair

        except (
            AuthenticationError,
            AccountError,
            AccountNotVerifiedError,
            AccountBannedError,
            AccountClosedError,
            AccountLoginError,
        ):
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during account creation for email: {email}")
            self.db_session.rollback()
            raise ErrorFactory.create_authentication_error(
                message="Account creation failed due to system error",
                context={"error_type": type(e).__name__, "error_message": str(e)},
            )

    # Note: Email lookup is now handled by Account.get_by_email() class method

    # Note: Account status validation is now handled by Account.can_login property

    # Note: Last login update is now handled by Account.update_last_login() method

    def get_user_by_id(self, user_id: UUID) -> Account | None:
        """
        Get user account by ID.

        Args:
            user_id: User ID

        Returns:
            Account or None if not found
        """
        try:
            statement = select(Account).where(Account.id == user_id, Account.is_deleted is False)
            return self.db_session.exec(statement).first()

        except Exception:
            logger.exception(f"Error fetching user by ID: {user_id}")
            return None

    def is_user_active(self, user_id: UUID) -> bool:
        """
        Check if user is active using Account model method.

        Args:
            user_id: User ID to check

        Returns:
            bool: True if user is active, False otherwise
        """
        user = self.get_user_by_id(user_id)
        return user is not None and user.is_active


def get_auth_service(db_session: Session) -> AuthService:
    """
    Factory function to create AuthService instance.

    Args:
        db_session: Database session

    Returns:
        AuthService: Configured authentication service
    """
    return AuthService(db_session)
