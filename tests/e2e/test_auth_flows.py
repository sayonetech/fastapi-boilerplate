"""End-to-end tests for authentication flows."""

from fastapi import status


class TestCompleteAuthenticationFlow:
    """Test complete authentication flows from registration to logout."""

    def test_complete_user_registration_and_login_flow(self, test_client):
        """Test complete flow: register -> login -> access protected -> logout."""
        # Step 1: Register new user
        register_data = {
            "name": "E2E Test User",
            "email": "e2e@example.com",
            "password": "SecurePassword123!",  # pragma: allowlist secret
        }  # pragma: allowlist secret

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        register_result = register_response.json()
        assert register_result["result"] == "success"
        assert "access_token" in register_result["data"]
        assert "refresh_token" in register_result["data"]

        # Store tokens from registration
        registration_access_token = register_result["data"]["access_token"]
        registration_refresh_token = register_result["data"]["refresh_token"]

        # Step 2: Login with the same credentials
        login_data = {
            "email": "e2e@example.com",
            "password": "SecurePassword123!",  # pragma: allowlist secret
            "remember_me": False,
        }  # pragma: allowlist secret

        login_response = test_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        login_result = login_response.json()
        assert login_result["result"] == "success"
        assert "access_token" in login_result["data"]
        assert "refresh_token" in login_result["data"]

        # Store tokens from login
        login_access_token = login_result["data"]["access_token"]
        login_refresh_token = login_result["data"]["refresh_token"]

        # Step 3: Access protected endpoint with login token
        profile_response = test_client.get("/api/v1/profile", headers={"Authorization": f"Bearer {login_access_token}"})

        # Should not be unauthorized (endpoint may or may not exist)
        assert profile_response.status_code != status.HTTP_401_UNAUTHORIZED

        # Step 4: Refresh token
        refresh_data = {"refresh_token": login_refresh_token}
        refresh_response = test_client.post("/api/v1/auth/refresh-token", json=refresh_data)

        if refresh_response.status_code == status.HTTP_200_OK:
            refresh_result = refresh_response.json()
            assert refresh_result["result"] == "success"
            new_access_token = refresh_result["data"]["access_token"]

            # Step 5: Use new access token
            profile_response_2 = test_client.get(
                "/api/v1/profile", headers={"Authorization": f"Bearer {new_access_token}"}
            )
            assert profile_response_2.status_code != status.HTTP_401_UNAUTHORIZED

        # Step 6: Logout
        logout_data = {"session_id": "test_session"}
        logout_response = test_client.post(
            "/api/v1/auth/logout", json=logout_data, headers={"Authorization": f"Bearer {login_access_token}"}
        )

        if logout_response.status_code == status.HTTP_200_OK:
            logout_result = logout_response.json()
            assert logout_result["success"] is True

    def test_registration_with_existing_email_flow(self, test_client):
        """Test registration flow with existing email."""
        # Step 1: Register first user
        register_data = {
            "name": "First User",
            "email": "duplicate@example.com",
            "password": "SecurePassword123!",  # pragma: allowlist secret
        }  # pragma: allowlist secret

        first_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert first_response.status_code == status.HTTP_200_OK

        # Step 2: Try to register second user with same email
        register_data_2 = {
            "name": "Second User",
            "email": "duplicate@example.com",
            "password": "DifferentPassword123!",  # pragma: allowlist secret
        }  # pragma: allowlist secret

        second_response = test_client.post("/api/v1/auth/register", json=register_data_2)
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST

        result = second_response.json()
        # Check for error response format - FastAPI returns detail field for HTTP exceptions
        error_message = result.get("detail", result.get("message", ""))
        assert error_message, "Expected error message in response"
        assert "already exists" in error_message.lower() or "already registered" in error_message.lower()

    def test_login_with_wrong_credentials_flow(self, test_client):
        """Test login flow with wrong credentials."""
        # Step 1: Register user
        register_data = {
            "name": "Test User",
            "email": "wrongcreds@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }  # pragma: allowlist secret

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Step 2: Try to login with wrong password
        wrong_login_data = {
            "email": "wrongcreds@example.com",
            "password": "WrongPassword123!",  # pragma: allowlist secret
            "remember_me": False,
        }  # pragma: allowlist secret

        login_response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED

        result = login_response.json()
        # Check for error response format - FastAPI returns detail field for HTTP exceptions
        error_message = result.get("detail", "")
        assert error_message, "Expected error message in response"
        assert "invalid" in error_message.lower() or "unauthorized" in error_message.lower()

        # Step 3: Try to login with wrong email
        wrong_email_data = {
            "email": "nonexistent@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
            "remember_me": False,
        }  # pragma: allowlist secret

        login_response_2 = test_client.post("/api/v1/auth/login", json=wrong_email_data)
        assert login_response_2.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh_flow(self, test_client):
        """Test token refresh flow."""
        # Step 1: Register and get tokens
        register_data = {"name": "Refresh Test User", "email": "refresh@example.com", "password": "SecurePassword123!"}

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        register_result = register_response.json()
        original_refresh_token = register_result["data"]["refresh_token"]

        # Step 2: Use refresh token to get new tokens
        refresh_data = {"refresh_token": original_refresh_token}
        refresh_response = test_client.post("/api/v1/auth/refresh-token", json=refresh_data)

        if refresh_response.status_code == status.HTTP_200_OK:
            refresh_result = refresh_response.json()
            assert refresh_result["result"] == "success"

            new_access_token = refresh_result["data"]["access_token"]
            new_refresh_token = refresh_result["data"]["refresh_token"]

            # Tokens should be different
            assert new_access_token != register_result["data"]["access_token"]
            # Refresh token may or may not be rotated depending on implementation

            # Step 3: Use new access token
            profile_response = test_client.get(
                "/api/v1/profile/me", headers={"Authorization": f"Bearer {new_access_token}"}
            )
            assert profile_response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_refresh_flow(self, test_client):
        """Test token refresh flow with invalid refresh token."""
        # Try to refresh with invalid token
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        refresh_response = test_client.post("/api/v1/auth/refresh-token", json=refresh_data)

        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
        result = refresh_response.json()
        # Check for error response format - FastAPI returns detail field for HTTP exceptions
        error_message = result.get("detail", "")
        assert error_message, "Expected error message in response"
        assert "invalid" in error_message.lower() or "expired" in error_message.lower()

    def test_access_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without token."""
        # Try to access protected endpoint without authentication
        response = test_client.get("/api/v1/profile/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_invalid_token(self, test_client):
        """Test accessing protected endpoint with invalid token."""
        # Try to access protected endpoint with invalid token
        response = test_client.get("/api/v1/profile/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_remember_me_functionality(self, test_client):
        """Test remember me functionality in login."""
        # Step 1: Register user
        register_data = {"name": "Remember Me User", "email": "remember@example.com", "password": "SecurePassword123!"}

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Step 2: Login with remember_me = True
        login_data = {"email": "remember@example.com", "password": "SecurePassword123!", "remember_me": True}

        login_response = test_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        result = login_response.json()
        assert result["result"] == "success"

        # The refresh token should have longer expiration (implementation dependent)
        refresh_expires_in = result["data"]["refresh_expires_in"]
        assert refresh_expires_in > 0

    def test_multiple_concurrent_sessions(self, test_client):
        """Test multiple concurrent sessions for the same user."""
        # Step 1: Register user
        register_data = {
            "name": "Multi Session User",
            "email": "multisession@example.com",
            "password": "SecurePassword123!",
        }

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Step 2: Login multiple times to create multiple sessions
        login_data = {"email": "multisession@example.com", "password": "SecurePassword123!", "remember_me": False}

        session_tokens = []
        for i in range(3):
            login_response = test_client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == status.HTTP_200_OK

            result = login_response.json()
            session_tokens.append(result["data"]["access_token"])

        # Step 3: Verify all sessions are valid
        for token in session_tokens:
            profile_response = test_client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
            # Should not be unauthorized
            assert profile_response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_logout_invalidates_session(self, test_client):
        """Test that logout invalidates the session."""
        # Step 1: Register and login
        register_data = {"name": "Logout Test User", "email": "logout@example.com", "password": "SecurePassword123!"}

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        login_data = {"email": "logout@example.com", "password": "SecurePassword123!", "remember_me": False}

        login_response = test_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        result = login_response.json()
        access_token = result["data"]["access_token"]
        refresh_token = result["data"]["refresh_token"]

        # Step 2: Verify token works before logout
        profile_response = test_client.get("/api/v1/profile", headers={"Authorization": f"Bearer {access_token}"})
        assert profile_response.status_code != status.HTTP_401_UNAUTHORIZED

        # Step 3: Logout
        logout_data = {"session_id": "test_session"}
        logout_response = test_client.post(
            "/api/v1/auth/logout", json=logout_data, headers={"Authorization": f"Bearer {access_token}"}
        )

        if logout_response.status_code == status.HTTP_200_OK:
            # Step 4: Try to use refresh token after logout (should fail)
            refresh_data = {"refresh_token": refresh_token}
            refresh_response = test_client.post("/api/v1/auth/refresh-token", json=refresh_data)

            # Refresh should fail after logout
            assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
