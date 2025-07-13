"""Authentication dependencies for FastAPI dependency injection."""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from ..models.auth import UserProfile
from ..services.auth_service import AuthService, get_auth_service
from ..services.token_service import get_token_service
from .db import get_session

logger = logging.getLogger(__name__)


def get_auth_service_dep(db_session: Session = Depends(get_session)) -> AuthService:
    """
    Get authentication service for dependency injection.

    Args:
        db_session: Database session

    Returns:
        AuthService: Authentication service instance
    """
    return get_auth_service(db_session)


def get_jwt_token_from_request(request: Request) -> str | None:
    """
    Extract JWT token from request headers.

    Args:
        request: FastAPI request object

    Returns:
        str or None: JWT token if found
    """
    # Try Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix

    # Try X-Access-Token header
    token_header = request.headers.get("X-Access-Token")
    if token_header:
        return token_header

    return None


def get_current_user_from_jwt(request: Request, session: Session = Depends(get_session)) -> UserProfile | None:
    """
    Get current user from JWT token (optional dependency).

    Args:
        request: FastAPI request object
        auth_service: Authentication service

    Returns:
        UserProfile or None: Current user if authenticated
    """
    try:
        token = get_jwt_token_from_request(request)
        if not token:
            return None

        token_service = get_token_service()
        claims = token_service.verify_token(token, "access")

        if not claims:
            return None

        # Get user from database to ensure it still exists and is active
        auth_service = get_auth_service(session)
        user = auth_service.get_user_by_id(claims.sub)
        if not user or not auth_service.is_user_active(user.id):
            return None

        # Create user profile from database user
        user_profile = UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            status=user.status,
            timezone=user.timezone,
            avatar=user.avatar,
            is_admin=user.is_admin,
            last_login_at=user.last_login_at,
            initialized_at=user.initialized_at,
            created_at=user.created_at,
        )

        logger.debug(f"Authenticated user via JWT: {user.email}")
        return user_profile

    except Exception as e:
        logger.exception("Error getting current user from JWT")
        return None


def get_current_user_from_jwt_required(
    request: Request, auth_service: AuthService = Depends(get_auth_service_dep)
) -> UserProfile:
    """
    Get current user from JWT token (required dependency).

    Args:
        request: FastAPI request object
        auth_service: Authentication service

    Returns:
        UserProfile: Current authenticated user

    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        token = get_jwt_token_from_request(request)
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please provide a valid access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_service = get_token_service()
        claims = token_service.verify_token(token, "access")

        if not claims:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired access token. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database to ensure it still exists and is active
        user = auth_service.get_user_by_id(claims.sub)
        if not user or not auth_service.is_user_active(user.id):
            raise HTTPException(
                status_code=401, detail="User account is no longer active.", headers={"WWW-Authenticate": "Bearer"}
            )

        # Create user profile from database user
        user_profile = UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            status=user.status,
            timezone=user.timezone,
            avatar=user.avatar,
            is_admin=user.is_admin,
            last_login_at=user.last_login_at,
            initialized_at=user.initialized_at,
            created_at=user.created_at,
        )

        logger.debug(f"Authenticated user via JWT: {user.email}")
        return user_profile

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception("Error getting current user from JWT")
        raise HTTPException(status_code=500, detail="Authentication service error") from e


def get_current_admin_user(current_user: UserProfile = Depends(get_current_user_from_jwt_required)) -> UserProfile:
    """
    Get current user and verify admin privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        UserProfile: Current admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    return current_user


def get_client_ip(request: Request) -> str | None:
    """
    Get client IP address from request.

    Args:
        request: FastAPI request object

    Returns:
        str or None: Client IP address
    """
    # Check for forwarded headers first (for reverse proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return None


# Type annotations for dependency injection
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service_dep)]
CurrentUser = Annotated[UserProfile, Depends(get_current_user_from_jwt_required)]
CurrentUserOptional = Annotated[Optional[UserProfile], Depends(get_current_user_from_jwt)]
CurrentAdminUser = Annotated[UserProfile, Depends(get_current_admin_user)]
ClientIP = Annotated[Optional[str], Depends(get_client_ip)]
