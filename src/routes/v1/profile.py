"""User profile routes for profile management and updates."""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request

from ...dependencies.auth import AuthServiceDep, CurrentUser
from ...dependencies.db import DatabaseSession
from ...entities.account import Account
from ...exceptions import AccountError, AuthenticationError
from ...libs.login import login_required
from ...models.auth import PasswordChangeRequest, PasswordChangeResponse, UserProfile
from ...models.profile import (
    ProfileStatsResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
)
from ..base_router import BaseRouter
from ..cbv import cbv, get, patch, post

logger = logging.getLogger(__name__)

profile_router = BaseRouter(
    prefix="/v1/profile",
    tags=["profile"],
)


@cbv(profile_router)
class ProfileController:
    """Profile controller for user profile management."""

    @get("/me", operation_id="get_current_user", response_model=UserProfile)
    async def get_current_user(
        self,
        current_user: CurrentUser,
    ) -> UserProfile:
        """
        Get current authenticated user profile.

        This endpoint returns the complete profile information for the
        currently authenticated user, including personal details, account
        status, and preferences.

        Args:
            current_user: Current authenticated user

        Returns:
            UserProfile: Current user information

        Raises:
            HTTPException: If user is not authenticated
        """
        logger.info(f"Profile requested for user: {current_user.email}")
        return current_user

    @get("/me-alt", operation_id="get_profile_with_decorator")
    @login_required
    async def get_profile_with_decorator(
        self,
        request: Request,
    ) -> dict[str, Any]:
        """
        Alternative profile endpoint demonstrating login_required decorator.

        This endpoint shows how to use the @login_required decorator instead of
        the CurrentUser dependency injection. The decorator ensures the user
        is authenticated before the endpoint is called.

        Args:
            request: FastAPI request object (required for decorator)

        Returns:
            dict: User profile information

        Raises:
            HTTPException: If authentication fails
        """
        # At this point, we know the user is authenticated due to @login_required
        # However, we need to get the user info again since the decorator doesn't
        # inject it as a parameter. In practice, you'd typically use CurrentUser dependency.

        try:
            from ...dependencies.auth import get_current_user_from_jwt
            from ...dependencies.db import get_session

            # Get user from JWT (we know it's valid due to decorator)
            db_session = next(get_session())
            try:
                current_user = get_current_user_from_jwt(request, db_session)

                if not current_user:
                    # This shouldn't happen due to @login_required, but just in case
                    raise HTTPException(status_code=401, detail="Authentication required")

                logger.info(f"Profile (decorator) requested for user: {current_user.email}")

                return {
                    "message": "Profile retrieved using @login_required decorator",
                    "user": {
                        "id": str(current_user.id),
                        "name": current_user.name,
                        "email": current_user.email,
                        "is_admin": current_user.is_admin,
                        "status": current_user.status,
                        "timezone": current_user.timezone,
                        "avatar": current_user.avatar,
                        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
                        "created_at": current_user.created_at.isoformat(),
                    },
                    "decorator_used": "login_required",
                    "note": "This demonstrates an alternative to CurrentUser dependency injection",
                }
            finally:
                db_session.close()

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error in profile endpoint with decorator")
            raise HTTPException(status_code=500, detail="Failed to retrieve profile") from e

    @post("/change-password", operation_id="change_password", response_model=PasswordChangeResponse)
    async def change_password(
        self,
        request: PasswordChangeRequest,
        current_user: CurrentUser,
        auth_service: AuthServiceDep,
    ) -> PasswordChangeResponse:
        """
        Change user password.

        This endpoint allows authenticated users to change their password
        by providing their current password and a new password.

        Args:
            request: Password change request with current and new passwords
            current_user: Current authenticated user
            auth_service: Authentication service

        Returns:
            PasswordChangeResponse: Password change confirmation

        Raises:
            HTTPException: If password change fails
        """
        try:
            logger.info(f"Password change requested for user: {current_user.email}")

            # Change password using auth service
            result = auth_service.change_password(
                user_id=current_user.id,
                current_password=request.current_password,
                new_password=request.new_password,
            )

            logger.info(f"Password changed successfully for user: {current_user.email}")
            return result

        except (AuthenticationError, AccountError) as e:
            logger.warning(f"Password change failed for {current_user.email}: {e.message}")

            if isinstance(e, AuthenticationError):
                raise HTTPException(status_code=401, detail=e.message)
            else:  # AccountError
                raise HTTPException(status_code=e.status_code, detail=e.message)

        except Exception as e:
            logger.exception(f"Unexpected error during password change for {current_user.email}")
            raise HTTPException(status_code=500, detail="Password change failed due to system error") from e

    @patch("/update", operation_id="update_profile", response_model=ProfileUpdateResponse)
    async def update_profile(
        self,
        request: ProfileUpdateRequest,
        current_user: CurrentUser,
        db_session: DatabaseSession,
    ) -> ProfileUpdateResponse:
        """
        Update user profile information.

        This endpoint allows authenticated users to update their profile
        information such as name, timezone, and avatar.

        Args:
            request: Profile update request
            current_user: Current authenticated user
            db_session: Database session

        Returns:
            ProfileUpdateResponse: Updated profile information

        Raises:
            HTTPException: If profile update fails
        """
        try:
            logger.info(f"Profile update requested for user: {current_user.email}")

            # Get the account from database
            account = db_session.get(Account, current_user.id)
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            # Update fields if provided
            updated_fields = []
            if request.name is not None:
                account.name = request.name.strip()
                updated_fields.append("name")

            if request.timezone is not None:
                account.timezone = request.timezone.strip() if request.timezone else None
                updated_fields.append("timezone")

            if request.avatar is not None:
                account.avatar = request.avatar.strip() if request.avatar else None
                updated_fields.append("avatar")

            # Update timestamp
            account.updated_at = datetime.now(UTC)

            # Commit changes
            db_session.commit()
            db_session.refresh(account)

            # Create updated user profile
            updated_user = UserProfile(
                id=account.id,
                name=account.name,
                email=account.email,
                status=account.status,
                timezone=account.timezone,
                avatar=account.avatar,
                is_admin=account.is_admin,
                last_login_at=account.last_login_at,
                initialized_at=account.initialized_at,
                created_at=account.created_at,
            )

            logger.info(f"Profile updated successfully for user: {current_user.email}, fields: {updated_fields}")

            # Create success message
            fields_message = ", ".join(updated_fields) if updated_fields else "none"
            success_message = f"Profile updated successfully. Updated fields: {fields_message}"

            return ProfileUpdateResponse(
                success=True,
                message=success_message,
                user=updated_user,
                updated_at=account.updated_at,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during profile update for {current_user.email}")
            raise HTTPException(status_code=500, detail="Profile update failed due to system error") from e

    @get("/stats", operation_id="get_profile_stats", response_model=ProfileStatsResponse)
    async def get_profile_stats(
        self,
        current_user: CurrentUser,
    ) -> ProfileStatsResponse:
        """
        Get user profile statistics and completion status.

        This endpoint provides insights about the user's profile including
        account age, activity status, and profile completion percentage.

        Args:
            current_user: Current authenticated user

        Returns:
            ProfileStatsResponse: Profile statistics

        Raises:
            HTTPException: If stats calculation fails
        """
        try:
            logger.info(f"Profile stats requested for user: {current_user.email}")

            # Calculate account age
            now = datetime.now(UTC)
            account_age_days = (now - current_user.created_at.replace(tzinfo=UTC)).days

            # Calculate last login days ago
            last_login_days_ago = None
            if current_user.last_login_at:
                last_login_days_ago = (now - current_user.last_login_at.replace(tzinfo=UTC)).days

            # Check if recently active (within 7 days)
            is_recently_active = last_login_days_ago is not None and last_login_days_ago <= 7

            # Calculate profile completion
            total_fields = 6  # name, email, timezone, avatar, status, is_admin
            completed_fields = 2  # name and email are always present

            if current_user.timezone:
                completed_fields += 1
            if current_user.avatar:
                completed_fields += 1
            if current_user.status:
                completed_fields += 1
            # is_admin is always set, so +1
            completed_fields += 1

            profile_completion = completed_fields / total_fields

            # Identify missing fields
            missing_fields = []
            if not current_user.timezone:
                missing_fields.append("timezone")
            if not current_user.avatar:
                missing_fields.append("avatar")

            return ProfileStatsResponse(
                user_id=current_user.id,
                account_age_days=account_age_days,
                last_login_days_ago=last_login_days_ago,
                is_recently_active=is_recently_active,
                profile_completion=profile_completion,
                missing_fields=missing_fields,
            )

        except Exception as e:
            logger.exception(f"Unexpected error getting profile stats for {current_user.email}")
            raise HTTPException(status_code=500, detail="Failed to retrieve profile statistics") from e
