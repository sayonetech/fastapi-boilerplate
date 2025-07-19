"""End-to-end tests for rate limiting scenarios."""

import time
from unittest.mock import patch

from fastapi import status


class TestLoginRateLimiting:
    """Test rate limiting for login attempts."""

    @patch("src.configs.madcrow_config")
    def test_login_rate_limiting_enabled(self, mock_config, test_client):
        """Test login rate limiting when enabled."""
        # Configure rate limiting
        mock_config.RATE_LIMITING_ENABLED = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 3
        mock_config.LOGIN_RATE_LIMIT_TIME_WINDOW = 300

        # Register a user first
        register_data = {
            "name": "Rate Limit Test User",
            "email": "ratelimit@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Prepare login data with wrong password
        wrong_login_data = {
            "email": "ratelimit@example.com",
            "password": "WrongPassword123!",  # pragma: allowlist secret
            "remember_me": False,
        }  # pragma: allowlist secret

        # Mock Redis to simulate rate limiting behavior
        with patch("src.dependencies.redis.get_redis_client") as mock_get_redis:
            mock_redis = mock_get_redis.return_value

            # Mock the RateLimiter class directly
            with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
                # Track call count to simulate rate limiting
                call_count = 0

                def mock_is_rate_limited(email, redis_client):
                    nonlocal call_count
                    return call_count >= 3

                def mock_increment(email, redis_client):
                    nonlocal call_count
                    call_count += 1

                # Configure the mock instance
                mock_instance = mock_rate_limiter_class.return_value
                mock_instance.is_rate_limited.side_effect = mock_is_rate_limited
                mock_instance.increment_rate_limit.side_effect = mock_increment
                mock_instance.get_time_until_reset.return_value = 300

                # Make 3 failed login attempts
                for i in range(3):
                    response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED

                # 4th attempt should be rate limited
                response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

                result = response.json()
                # Rate limit response is wrapped in 'detail' field
                assert result["detail"]["result"] == "error"
                assert (
                    "rate limit" in result["detail"]["message"].lower()
                    or "too many" in result["detail"]["message"].lower()
                )
                assert result["detail"]["error_code"] == "RATE_LIMIT_EXCEEDED"

    @patch("src.configs.madcrow_config")
    def test_login_rate_limiting_disabled(self, mock_config, test_client):
        """Test login behavior when rate limiting is disabled."""
        # Disable rate limiting
        mock_config.RATE_LIMITING_ENABLED = False

        # Register a user first
        register_data = {
            "name": "No Rate Limit User",
            "email": "noratelimit@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Prepare login data with wrong password
        wrong_login_data = {
            "email": "noratelimit@example.com",
            "password": "WrongPassword123!",  # pragma: allowlist secret
            "remember_me": False,
        }  # pragma: allowlist secret

        # Make multiple failed login attempts
        for i in range(10):  # More than typical rate limit
            response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
            # Should always be 401 (unauthorized), never 429 (rate limited)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.configs.madcrow_config")
    def test_rate_limiting_reset_after_successful_login(self, mock_config, test_client):
        """Test that rate limiting is reset after successful login."""
        # Configure rate limiting
        mock_config.RATE_LIMITING_ENABLED = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 3
        mock_config.LOGIN_RATE_LIMIT_TIME_WINDOW = 300

        # Register a user first
        register_data = {
            "name": "Reset Rate Limit User",
            "email": "resetrate@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        with patch("src.dependencies.redis.get_redis_client") as mock_get_redis:
            mock_redis = mock_get_redis.return_value

            with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
                mock_instance = mock_rate_limiter_class.return_value
                mock_instance.is_rate_limited.return_value = False
                mock_instance.get_time_until_reset.return_value = 300

                wrong_login_data = {
                    "email": "resetrate@example.com",
                    "password": "WrongPassword123!",  # pragma: allowlist secret
                    "remember_me": False,
                }

                # Make 2 failed attempts
                for i in range(2):
                    response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED

                # Now make successful login
                correct_login_data = {
                    "email": "resetrate@example.com",
                    "password": "CorrectPassword123!",  # pragma: allowlist secret
                    "remember_me": False,
                }

                response = test_client.post("/api/v1/auth/login", json=correct_login_data)
                assert response.status_code == status.HTTP_200_OK

                # Verify reset_rate_limit was called
                mock_instance.reset_rate_limit.assert_called()

    @patch("src.configs.madcrow_config")
    def test_rate_limiting_per_email(self, mock_config, test_client):
        """Test that rate limiting is applied per email address."""
        # Configure rate limiting
        mock_config.RATE_LIMITING_ENABLED = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 2
        mock_config.LOGIN_RATE_LIMIT_TIME_WINDOW = 300

        # Register two users
        users = [
            {"name": "User One", "email": "user1@example.com", "password": "Password123!"},  # pragma: allowlist secret
            {"name": "User Two", "email": "user2@example.com", "password": "Password123!"},  # pragma: allowlist secret
        ]

        for user_data in users:
            response = test_client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_200_OK

        with patch("src.dependencies.redis.get_redis_client") as mock_get_redis:
            mock_redis = mock_get_redis.return_value

            with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
                # Mock rate limiter to track calls per email
                rate_limit_calls = {}

                def mock_is_rate_limited(email, redis_client):
                    count = rate_limit_calls.get(email, 0)
                    return count >= 2  # Rate limit after 2 attempts

                def mock_increment(email, redis_client):
                    rate_limit_calls[email] = rate_limit_calls.get(email, 0) + 1

                mock_instance = mock_rate_limiter_class.return_value
                mock_instance.is_rate_limited.side_effect = mock_is_rate_limited
                mock_instance.increment_rate_limit.side_effect = mock_increment
                mock_instance.get_time_until_reset.return_value = 300

                # Make failed attempts for user1
                wrong_data_user1 = {
                    "email": "user1@example.com",
                    "password": "WrongPassword",  # pragma: allowlist secret
                    "remember_me": False,
                }  # pragma: allowlist secret

                # First 2 attempts for user1 should fail but not be rate limited
                for i in range(2):
                    response = test_client.post("/api/v1/auth/login", json=wrong_data_user1)
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED

                # 3rd attempt for user1 should be rate limited
                response = test_client.post("/api/v1/auth/login", json=wrong_data_user1)
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

                # But user2 should still be able to login
                wrong_data_user2 = {
                    "email": "user2@example.com",
                    "password": "WrongPassword",  # pragma: allowlist secret
                    "remember_me": False,
                }  # pragma: allowlist secret

                response = test_client.post("/api/v1/auth/login", json=wrong_data_user2)
                assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Not rate limited

    @patch("src.configs.madcrow_config")
    def test_rate_limiting_time_window(self, mock_config, test_client):
        """Test rate limiting time window behavior."""
        # Configure short time window for testing
        mock_config.RATE_LIMITING_ENABLED = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 2
        mock_config.LOGIN_RATE_LIMIT_TIME_WINDOW = 1  # 1 second for testing

        # Register a user
        register_data = {
            "name": "Time Window User",
            "email": "timewindow@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        with patch("src.dependencies.redis.get_redis_client") as mock_get_redis:
            mock_redis = mock_get_redis.return_value

            with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
                # Simulate time-based rate limiting
                attempt_times = []

                def mock_is_rate_limited(email, redis_client):
                    current_time = time.time()
                    # Remove attempts older than 1 second
                    attempt_times[:] = [t for t in attempt_times if current_time - t < 1]
                    return len(attempt_times) >= 2

                def mock_increment(email, redis_client):
                    attempt_times.append(time.time())

                mock_instance = mock_rate_limiter_class.return_value
                mock_instance.is_rate_limited.side_effect = mock_is_rate_limited
                mock_instance.increment_rate_limit.side_effect = mock_increment
                mock_instance.get_time_until_reset.return_value = 1

                wrong_login_data = {
                    "email": "timewindow@example.com",
                    "password": "WrongPassword",  # pragma: allowlist secret
                    "remember_me": False,
                }

                # Make 2 failed attempts quickly
                for i in range(2):
                    response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
                    assert response.status_code == status.HTTP_401_UNAUTHORIZED

                # 3rd attempt should be rate limited
                response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

                # Wait for time window to pass
                time.sleep(1.1)

                # Should be able to attempt again after time window
                response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
                assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Not rate limited

    def test_rate_limiting_headers(self, test_client):
        """Test that rate limiting responses include appropriate headers."""
        # This test depends on the implementation including rate limit headers

        # Register a user
        register_data = {
            "name": "Headers Test User",
            "email": "headers@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }  # pragma: allowlist secret

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Mock rate limiting to trigger 429 response
        with patch("src.services.auth_service.AuthService.authenticate_user") as mock_auth:
            from src.exceptions import RateLimitExceededError

            mock_auth.side_effect = RateLimitExceededError(
                identifier="headers@example.com", max_attempts=5, time_window=300, retry_after=120
            )

            wrong_login_data = {
                "email": "headers@example.com",
                "password": "WrongPassword",  # pragma: allowlist secret
                "remember_me": False,
            }  # pragma: allowlist secret

            response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

            # Check for rate limiting headers
            assert "Retry-After" in response.headers

            # Optional: Check for other rate limiting headers if implemented
            # assert "X-RateLimit-Limit" in response.headers
            # assert "X-RateLimit-Remaining" in response.headers
            # assert "X-RateLimit-Reset" in response.headers

    def test_rate_limiting_with_different_ips(self, test_client):
        """Test rate limiting behavior with different IP addresses."""
        # This test would require mocking IP detection
        # Implementation depends on how client IP is determined

        register_data = {
            "name": "IP Test User",
            "email": "iptest@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }  # pragma: allowlist secret

        register_response = test_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Mock different client IPs
        with patch("src.dependencies.auth.get_client_ip") as mock_get_ip:
            # Test with IP 1
            mock_get_ip.return_value = "192.168.1.1"

            wrong_login_data = {
                "email": "iptest@example.com",
                "password": "WrongPassword",  # pragma: allowlist secret
                "remember_me": False,
            }  # pragma: allowlist secret

            # Make some failed attempts from IP 1
            for i in range(3):
                response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
                # Should get 401 (unauthorized) not 429 (rate limited) for now
                assert response.status_code == status.HTTP_401_UNAUTHORIZED

            # Test with IP 2
            mock_get_ip.return_value = "192.168.1.2"

            # Should still be able to attempt from different IP
            response = test_client.post("/api/v1/auth/login", json=wrong_login_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.configs.madcrow_config")
    def test_emergency_lockdown_mode(self, mock_config, test_client):
        """Test emergency lockdown mode with max_attempts=0."""
        # Configure emergency lockdown mode
        mock_config.RATE_LIMIT_LOGIN_ENABLED = True
        mock_config.RATE_LIMIT_LOGIN_MAX_ATTEMPTS = 0  # Emergency lockdown
        mock_config.RATE_LIMIT_LOGIN_TIME_WINDOW = 300

        # Register a user first
        register_data = {
            "name": "Lockdown Test User",
            "email": "lockdown@example.com",
            "password": "CorrectPassword123!",  # pragma: allowlist secret
        }
        response = test_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == status.HTTP_200_OK

        # Mock rate limiter to simulate emergency lockdown
        with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
            mock_rate_limiter = mock_rate_limiter_class.return_value

            # In emergency lockdown mode, is_rate_limited should always return True
            mock_rate_limiter.is_rate_limited.return_value = True
            mock_rate_limiter.max_attempts = 0
            mock_rate_limiter.time_window = 300

            # Try to login with correct credentials - should be blocked due to lockdown
            login_data = {
                "email": "lockdown@example.com",
                "password": "CorrectPassword123!",  # pragma: allowlist secret
            }

            response = test_client.post("/api/v1/auth/login", json=login_data)

            # Should be rate limited even with correct credentials
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

            response_data = response.json()
            assert response_data["detail"]["rate_limit_info"]["max_attempts"] == 0
            assert response_data["detail"]["rate_limit_info"]["is_limited"] is True
            assert "Retry-After" in response.headers
