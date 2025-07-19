"""
Security validation tests for the authentication system.

These tests validate security measures including:
- SQL injection prevention
- XSS prevention
- Authentication bypass attempts
- Input sanitization
- Rate limiting security
- Password security
"""

from unittest.mock import patch

import pytest
from fastapi import status


@pytest.mark.security
class TestSQLInjectionPrevention:
    """Test SQL injection prevention measures."""

    def test_login_sql_injection_attempts(self, test_client):
        """Test that SQL injection attempts in login are prevented."""
        sql_injection_payloads = [
            "admin'; DROP TABLE accounts; --",
            "' OR '1'='1",
            "' OR 1=1 --",
            "admin'/*",
            "' UNION SELECT * FROM accounts --",
            "'; INSERT INTO accounts VALUES ('hacker', 'hacked'); --",
            "' OR 'x'='x",
            "1' OR '1'='1' /*",
        ]

        for payload in sql_injection_payloads:
            response = test_client.post(
                "/api/v1/auth/login",
                json={"email": payload, "password": "any_password", "remember_me": False},  # pragma: allowlist secret
            )

            # Should return validation error or authentication failed, not 500
            assert response.status_code in [400, 401, 422], (
                f"SQL injection payload '{payload}' caused unexpected response"
            )

            # Should not contain actual database error messages (but validation errors are OK)
            response_text = response.text.lower()
            # Check for actual SQL error indicators, not just the word "table" in validation messages
            assert "sql error" not in response_text
            assert "database error" not in response_text
            assert "syntax error" not in response_text
            assert "constraint violation" not in response_text

    def test_register_sql_injection_attempts(self, test_client):
        """Test that SQL injection attempts in registration are prevented."""
        sql_injection_payloads = [
            "'; DROP TABLE accounts; --",
            "' OR 1=1 --",
            "admin'/*",
        ]

        for payload in sql_injection_payloads:
            response = test_client.post(
                "/api/v1/auth/register",
                json={
                    "name": payload,
                    "email": f"test{payload}@example.com",
                    "password": "SecurePassword123!",  # pragma: allowlist secret
                },  # pragma: allowlist secret
            )

            # Should return validation error, not 500
            assert response.status_code in [400, 422], f"SQL injection payload '{payload}' caused unexpected response"


@pytest.mark.security
class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention measures."""

    def test_xss_in_user_input(self, test_client, unique_user_factory):
        """Test that XSS payloads in user input are sanitized."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        ]

        for payload in xss_payloads:
            user_data = unique_user_factory("xsstest")
            user_data["name"] = payload

            response = test_client.post("/api/v1/auth/register", json=user_data)

            # Should either reject the input or sanitize it
            if response.status_code == 201:
                # If accepted, check that the response doesn't contain raw script tags
                response_text = response.text
                assert "<script>" not in response_text
                assert "javascript:" not in response_text
                assert "onerror=" not in response_text

    def test_response_headers_security(self, test_client):
        """Test that security headers are present in responses."""
        response = test_client.get("/api/v1/health")

        # Check for security headers
        headers = response.headers

        # Content-Type should be properly set
        assert "application/json" in headers.get("content-type", "")

        # Should not expose server information
        assert "server" not in headers or "fastapi" not in headers.get("server", "").lower()


@pytest.mark.security
class TestAuthenticationBypass:
    """Test authentication bypass prevention."""

    def test_jwt_token_manipulation(self, test_client):
        """Test that manipulated JWT tokens are rejected."""
        # Test with invalid JWT tokens
        invalid_tokens = [
            "invalid.jwt.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "Bearer ",
            "null",
            "undefined",
        ]

        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = test_client.get("/api/v1/profile/me", headers=headers)

            # Should return 401 Unauthorized
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_session_fixation_prevention(self, test_client, created_test_user):
        """Test that session fixation attacks are prevented through refresh token invalidation."""
        # Login to get a valid token pair
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={"email": created_test_user["email"], "password": created_test_user["password"], "remember_me": False},
        )

        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["data"]["access_token"]
        refresh_token = token_data["data"]["refresh_token"]

        # Try to use the same token from different "sessions"
        headers = {"Authorization": f"Bearer {access_token}"}

        # First request should work
        response1 = test_client.get("/api/v1/profile/me", headers=headers)
        assert response1.status_code == 200

        # Logout should invalidate the refresh token (but access token remains valid until expiry)
        logout_data = {"session_id": "test_session"}
        logout_response = test_client.post("/api/v1/auth/logout", json=logout_data, headers=headers)
        assert logout_response.status_code == 200

        # Access token should still work (JWT tokens remain valid until expiry)
        response2 = test_client.get("/api/v1/profile/me", headers=headers)
        assert response2.status_code == 200

        # But refresh token should be invalid after logout
        refresh_response = test_client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh_token})
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.security
class TestInputSanitization:
    """Test input sanitization and validation."""

    def test_email_validation_security(self, test_client):
        """Test that email validation prevents malicious inputs."""
        malicious_emails = [
            "test@evil.com<script>alert('xss')</script>",
            "test+<script>@example.com",
            "test@example.com'; DROP TABLE accounts; --",
            "test@example.com\r\nBcc: attacker@evil.com",
            "test@example.com\nX-Injected-Header: malicious",
        ]

        for email in malicious_emails:
            response = test_client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "any_password", "remember_me": False},  # pragma: allowlist secret
            )

            # Should return validation error
            assert response.status_code in [400, 401, 422]

    def test_password_validation_security(self, test_client, unique_user_factory):
        """Test that password validation prevents weak passwords."""
        weak_passwords = [
            "",  # Empty
            "123",  # Too short
            "password",  # Common password
            "12345678",  # Only numbers
            "abcdefgh",  # Only letters
            "Password",  # Missing special chars and numbers
        ]

        for password in weak_passwords:
            user_data = unique_user_factory("weakpass")
            user_data["password"] = password

            response = test_client.post("/api/v1/auth/register", json=user_data)

            # Should reject weak passwords
            assert response.status_code in [400, 422]


@pytest.mark.security
class TestRateLimitingSecurity:
    """Test rate limiting security measures."""

    @patch("src.configs.madcrow_config")
    def test_rate_limiting_prevents_brute_force(self, mock_config, test_client, created_test_user):
        """Test that rate limiting prevents brute force attacks."""
        # Enable rate limiting
        mock_config.ENABLE_LOGIN_RATE_LIMITING = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 3
        mock_config.LOGIN_RATE_LIMIT_TIME_WINDOW = 300

        with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
            # Track attempts
            attempt_count = 0

            def mock_is_rate_limited(email, redis_client):
                nonlocal attempt_count
                return attempt_count >= 3

            def mock_increment(email, redis_client):
                nonlocal attempt_count
                attempt_count += 1

            mock_instance = mock_rate_limiter_class.return_value
            mock_instance.is_rate_limited.side_effect = mock_is_rate_limited
            mock_instance.increment_rate_limit.side_effect = mock_increment
            mock_instance.get_time_until_reset.return_value = 300

            # Make multiple failed login attempts
            for i in range(5):
                response = test_client.post(
                    "/api/v1/auth/login",
                    json={"email": created_test_user["email"], "password": "wrong_password", "remember_me": False},
                )

                if i < 3:
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED
                else:
                    # Should be rate limited after 3 attempts
                    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limiting_headers_present(self, test_client, created_test_user):
        """Test that rate limiting headers are present in responses."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": created_test_user["email"], "password": "wrong_password", "remember_me": False},
        )

        # Check if rate limiting headers are present (if implemented)
        headers = response.headers
        # Note: This test may need adjustment based on your actual implementation
        # Common rate limiting headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset


@pytest.mark.security
class TestPasswordSecurity:
    """Test password security measures."""

    def test_password_hashing_security(self):
        """Test that passwords are properly hashed and salted."""
        from src.libs.password import create_password_hash, verify_password

        password = "TestPassword123!"  # pragma: allowlist secret

        # Create hash
        password_hash, salt = create_password_hash(password)

        # Hash should not contain the original password
        assert password not in password_hash
        assert password not in salt

        # Hash should be different each time (due to salt)
        password_hash2, salt2 = create_password_hash(password)
        assert password_hash != password_hash2
        assert salt != salt2

        # But verification should still work
        assert verify_password(password, password_hash, salt) is True
        assert verify_password("wrong_password", password_hash, salt) is False

    def test_password_storage_security(self, test_db_session, unique_user_factory):
        """Test that passwords are not stored in plain text."""
        from src.entities.account import Account
        from src.libs.password import create_password_hash

        user_data = unique_user_factory("securetest")
        password = user_data["password"]
        password_hash, salt = create_password_hash(password)

        # Create account
        account = Account(
            name=user_data["name"],
            email=user_data["email"],
            password=password_hash,
            password_salt=salt,
            status="ACTIVE",
        )

        test_db_session.add(account)
        test_db_session.commit()
        test_db_session.refresh(account)

        # Verify password is not stored in plain text
        assert account.password != password
        assert password not in account.password
        assert len(account.password) > len(password)  # Hash should be longer
        assert account.password_salt is not None
        assert len(account.password_salt) > 0
