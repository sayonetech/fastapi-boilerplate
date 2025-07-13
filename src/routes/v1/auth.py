"""Authentication routes for login, logout, and session management."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request

from ...dependencies.auth import AuthServiceDep, ClientIP, CurrentUser
from ...dependencies.redis import RedisServiceDep
from ...exceptions import AccountError, AuthenticationError
from ...models.auth import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    SessionInfo,
    SessionValidationResponse,
    UserProfile,
)
from ...models.token import LoginResponse as TokenLoginResponse
from ...models.token import (
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
)
from ...services.token_service import get_token_service
from ..base_router import BaseRouter
from ..cbv import cbv, get, post

logger = logging.getLogger(__name__)

auth_router = BaseRouter(
    prefix="/v1/auth",
    tags=["authentication"],
)


@cbv(auth_router)
class AuthController:
    """Authentication controller for login, logout, and session management."""

    @post("/login", operation_id="login", response_model=TokenLoginResponse)
    async def login(
        self,
        request: LoginRequest,
        auth_service: AuthServiceDep,
        client_ip: ClientIP,
    ) -> TokenLoginResponse:
        """
        Authenticate user and create session.

        This endpoint provides secure login functionality:
        1. Validate email and password
        2. Check account status
        3. Generate JWT tokens
        4. Return token pair

        Args:
            request: Login request with email and password
            auth_service: Authentication service
            client_ip: Client IP address

        Returns:
            TokenLoginResponse: Token pair response

        Raises:
            HTTPException: If authentication fails
        """
        try:
            logger.info(f"Login attempt for email: {request.email}")

            # Authenticate user and get token pair
            token_pair = auth_service.authenticate_user(
                email=request.email, password=request.password, login_ip=client_ip
            )

            logger.info(f"Successful login for user: {request.email}")

            # Return standard response
            return TokenLoginResponse(result="success", data=token_pair)

        except (AuthenticationError, AccountError) as e:
            # Convert our custom errors to HTTP exceptions
            logger.warning(f"Login failed for {request.email}: {e.message}")

            if isinstance(e, AuthenticationError):
                raise HTTPException(status_code=401, detail=e.message)
            else:  # AccountError
                raise HTTPException(status_code=e.status_code, detail=e.message)

        except Exception as e:
            logger.exception(f"Unexpected error during login for {request.email}")
            raise HTTPException(status_code=500, detail="Login failed due to system error") from e

    @post("/register", operation_id="register", response_model=RegisterResponse)
    async def register(
        self,
        request: RegisterRequest,
        auth_service: AuthServiceDep,
        client_ip: ClientIP,
    ) -> RegisterResponse:
        """
        Register new user account.

        This endpoint provides secure user registration:
        1. Validate input data
        2. Check password strength
        3. Create account with secure password hashing
        4. Return token pair

        Args:
            request: Registration request with name, email, password
            auth_service: Authentication service
            client_ip: Client IP address

        Returns:
            RegisterResponse: Token pair response

        Raises:
            HTTPException: If registration fails
        """
        try:
            logger.info(f"Registration attempt for email: {request.email}")

            # Create account and get token pair
            token_pair = auth_service.create_account(
                name=request.name,
                email=request.email,
                password=request.password,
                is_admin=False,  # Regular users are not admin by default
            )

            logger.info(f"Successful registration for user: {request.email}")

            # Return standard response
            return RegisterResponse(result="success", data=token_pair)

        except (AuthenticationError, AccountError) as e:
            # Convert our custom errors to HTTP exceptions
            logger.warning(f"Registration failed for {request.email}: {e.message}")

            if isinstance(e, AuthenticationError):
                raise HTTPException(status_code=400, detail=e.message)
            else:  # AccountError
                raise HTTPException(status_code=e.status_code, detail=e.message)

        except Exception as e:
            logger.exception(f"Unexpected error during registration for {request.email}")
            raise HTTPException(status_code=500, detail="Registration failed due to system error") from e

    @post("/logout", operation_id="logout", response_model=LogoutResponse)
    async def logout(
        self,
        request: LogoutRequest,
        current_user: CurrentUser,
        redis_service: RedisServiceDep,
    ) -> LogoutResponse:
        """
        Logout user and invalidate refresh token.

        Args:
            request: Logout request
            current_user: Current authenticated user
            redis_service: Redis service

        Returns:
            LogoutResponse: Logout confirmation
        """
        try:
            # Get token service and logout user (delete refresh token)
            token_service = get_token_service(redis_service.client)
            token_service.logout(str(current_user.id))

            logger.info(f"User logged out: {current_user.email}")

            return LogoutResponse(success=True, message="Logout successful", logged_out_at=datetime.now(UTC))

        except Exception:
            logger.exception("Error during logout")
            # Don't fail logout even if there's an error
            return LogoutResponse(
                success=True, message="Logout completed (with warnings)", logged_out_at=datetime.now(UTC)
            )

    @get("/session/validate", operation_id="validate_session", response_model=SessionValidationResponse)
    async def validate_session(
        self,
        request: Request,
        redis_service: RedisServiceDep,
    ) -> SessionValidationResponse:
        """
        Validate current JWT token and return user information.

        Args:
            request: FastAPI request object
            redis_service: Redis service

        Returns:
            SessionValidationResponse: Session validation result
        """
        try:
            # Try to get current user from JWT token
            from ...dependencies.auth import get_current_user_from_jwt

            user = get_current_user_from_jwt(request)

            if not user:
                return SessionValidationResponse(valid=False, user=None, session=None, message="No valid token found")

            # Create mock session info (since we're using JWT tokens now)
            session_info = SessionInfo(
                session_id="jwt_token",  # Placeholder
                expires_at=datetime.now(UTC) + timedelta(hours=1),  # Access token expiry
                remember_me=False,  # Not applicable for JWT
            )

            return SessionValidationResponse(valid=True, user=user, session=session_info, message="Token is valid")

        except Exception:
            logger.exception("Error validating token")
            return SessionValidationResponse(valid=False, user=None, session=None, message="Token validation error")

    @post("/refresh-token", operation_id="refresh_token", response_model=RefreshTokenResponse)
    async def refresh_token(
        self,
        request: RefreshTokenRequest,
        redis_service: RedisServiceDep,
    ) -> RefreshTokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            request: Refresh token request
            redis_service: Redis service

        Returns:
            RefreshTokenResponse: New token pair

        Raises:
            HTTPException: If refresh token is invalid
        """
        try:
            token_service = get_token_service(redis_service.client)

            # Refresh token pair
            new_token_pair = token_service.refresh_token_pair(request.refresh_token)

            if not new_token_pair:
                raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

            logger.info("Token refreshed successfully")

            return RefreshTokenResponse(result="success", data=new_token_pair)

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.exception("Error refreshing token")
            raise HTTPException(status_code=500, detail="Token refresh failed") from e

    @get("/me", operation_id="get_current_user", response_model=UserProfile)
    async def get_current_user(
        self,
        current_user: CurrentUser,
    ) -> UserProfile:
        """
        Get current authenticated user profile.

        Args:
            current_user: Current authenticated user

        Returns:
            UserProfile: Current user information
        """
        return current_user

    @post("/logout-all", operation_id="logout_all_sessions")
    async def logout_all_sessions(
        self,
        current_user: CurrentUser,
        redis_service: RedisServiceDep,
    ) -> dict[str, Any]:
        """
        Logout from all sessions for the current user (invalidate refresh token).

        Args:
            current_user: Current authenticated user
            redis_service: Redis service

        Returns:
            dict: Logout result
        """
        try:
            # Delete user's refresh token (equivalent to logging out from all sessions)
            token_service = get_token_service(redis_service.client)
            token_service.logout(str(current_user.id))

            logger.info(f"Logged out all sessions for user: {current_user.email}")

            return {
                "success": True,
                "message": "Logged out from all sessions",
                "sessions_deleted": 1,  # Only one refresh token per user
                "logged_out_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.exception(f"Error logging out all sessions for user: {current_user.email}")
            raise HTTPException(status_code=500, detail="Failed to logout from all sessions") from e
