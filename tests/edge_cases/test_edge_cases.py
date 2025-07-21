"""
Edge case tests for the authentication system.

These tests cover unusual scenarios and edge cases including:
- Boundary conditions
- Race conditions
- Error handling edge cases
- Data corruption scenarios
- Network failure simulation
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from sqlalchemy.exc import IntegrityError


@pytest.mark.edge_cases
class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    def test_maximum_email_length(self, test_client, unique_user_factory):
        """Test handling of maximum email length."""
        # Create very long email (near typical database limits)
        long_local_part = "a" * 64  # Maximum local part length
        long_domain = "b" * 60 + ".com"  # Long domain
        long_email = f"{long_local_part}@{long_domain}"

        user_data = unique_user_factory("longmail")
        user_data["email"] = long_email

        response = test_client.post("/api/v1/auth/register", json=user_data)

        # Should either accept or reject gracefully
        assert response.status_code in [200, 201, 400, 422]

        # If rejected, should have clear error message
        if response.status_code in [400, 422]:
            response_data = response.json()
            assert "email" in str(response_data).lower()

    def test_maximum_name_length(self, test_client, unique_user_factory):
        """Test handling of maximum name length."""
        user_data = unique_user_factory("longname")
        user_data["name"] = "A" * 1000  # Very long name

        response = test_client.post("/api/v1/auth/register", json=user_data)

        # Should reject gracefully
        assert response.status_code in [400, 422]

    def test_minimum_password_requirements(self, test_client, unique_user_factory):
        """Test password minimum requirements edge cases."""
        edge_case_passwords = [
            "A1!",  # Exactly minimum length if 3 chars
            "A1!a",  # Just above minimum
            "Aa1!",  # Exactly minimum with all requirements
            "A" * 128 + "1!a",  # Very long password
        ]

        for password in edge_case_passwords:
            user_data = unique_user_factory("passtest")
            user_data["password"] = password

            response = test_client.post("/api/v1/auth/register", json=user_data)

            # Should handle gracefully
            assert response.status_code in [200, 201, 400, 422]

    def test_unicode_handling(self, test_client, unique_user_factory):
        """Test handling of Unicode characters in input."""
        unicode_test_cases = [
            {"name": "José María", "email": "jose@example.com"},
            {"name": "李小明", "email": "li@example.com"},
            {"name": "محمد", "email": "mohammed@example.com"},
            {"name": "🙂 User", "email": "emoji@example.com"},
        ]

        for test_case in unicode_test_cases:
            user_data = unique_user_factory("unicode")
            user_data.update(test_case)

            response = test_client.post("/api/v1/auth/register", json=user_data)

            # Should handle Unicode gracefully
            assert response.status_code in [200, 201, 400, 422]


@pytest.mark.edge_cases
class TestRaceConditions:
    """Test race condition scenarios."""

    def test_concurrent_user_registration_same_email(self, test_client, unique_user_factory):
        """Test concurrent registration attempts with the same email."""
        user_data = unique_user_factory("racetest")

        def register_user():
            return test_client.post("/api/v1/auth/register", json=user_data)

        # Try to register the same user concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_user) for _ in range(5)]
            responses = [future.result() for future in as_completed(futures)]

        # Only one should succeed, others should fail with appropriate error
        success_count = sum(1 for r in responses if r.status_code in [200, 201])
        error_count = sum(1 for r in responses if r.status_code in [400, 409, 422])

        assert success_count == 1, f"Expected 1 success, got {success_count}"
        assert error_count == 4, f"Expected 4 errors, got {error_count}"

    def test_concurrent_login_attempts_same_user(self, test_client, created_test_user):
        """Test concurrent login attempts for the same user."""
        login_data = {
            "email": created_test_user["email"],
            "password": created_test_user["password"],
            "remember_me": False,
        }

        def login_user():
            return test_client.post("/api/v1/auth/login", json=login_data)

        # Multiple concurrent logins should all succeed
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_user) for _ in range(5)]
            responses = [future.result() for future in as_completed(futures)]

        # All should succeed (or at least most should)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 4, f"Expected at least 4 successes, got {success_count}"

    @patch("src.configs.madcrow_config")
    def test_race_condition_in_rate_limiting(self, mock_config, test_client, created_test_user):
        """Test race conditions in rate limiting logic."""
        mock_config.ENABLE_LOGIN_RATE_LIMITING = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 2

        login_data = {"email": created_test_user["email"], "password": "wrong_password", "remember_me": False}

        with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
            attempt_count = 0
            lock = threading.Lock()

            def mock_is_rate_limited(email, redis_client):
                with lock:
                    return attempt_count >= 2

            def mock_increment(email, redis_client):
                nonlocal attempt_count
                with lock:
                    attempt_count += 1
                    # Simulate some processing time
                    time.sleep(0.01)

            mock_instance = mock_rate_limiter_class.return_value
            mock_instance.is_rate_limited.side_effect = mock_is_rate_limited
            mock_instance.increment_rate_limit.side_effect = mock_increment
            mock_instance.get_time_until_reset.return_value = 300

            def make_login_attempt():
                return test_client.post("/api/v1/auth/login", json=login_data)

            # Make concurrent attempts that should trigger rate limiting
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_login_attempt) for _ in range(5)]
                responses = [future.result() for future in as_completed(futures)]

            # Should have some rate limited responses
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            auth_failed_count = sum(1 for r in responses if r.status_code == 401)

            # Rate limiting should work even under concurrent load
            assert rate_limited_count > 0, "Rate limiting should trigger under concurrent load"


@pytest.mark.edge_cases
class TestErrorHandling:
    """Test error handling edge cases."""

    def test_malformed_json_requests(self, test_client):
        """Test handling of malformed JSON requests."""
        malformed_payloads = [
            # Missing closing brace  # pragma: allowlist secret
            '{"email": "test@example.com", "password": "incomplete"',  # pragma: allowlist secret
            '{"email": "test@example.com", "password":}',  # Missing value
            # Invalid syntax  # pragma: allowlist secret
            '{"email": "test@example.com", "password": "test", extra}',  # pragma: allowlist secret
            "",  # Empty payload
            "not json at all",  # Not JSON
            '{"email": null, "password": null}',  # Null values
        ]

        for payload in malformed_payloads:
            response = test_client.post(
                "/api/v1/auth/login", data=payload, headers={"Content-Type": "application/json"}
            )

            # Should return 422 (validation error) or 400 (bad request)
            assert response.status_code in [400, 422]

    def test_missing_content_type_header(self, test_client, unique_user_factory):
        """Test handling of requests without Content-Type header."""
        user_data = unique_user_factory("noheader")

        response = test_client.post(
            "/api/v1/auth/register",
            json=user_data,
            headers={},  # No Content-Type header
        )

        # FastAPI should handle this gracefully
        assert response.status_code in [200, 201, 400, 415, 422]

    def test_extremely_large_request_payload(self, test_client):
        """Test handling of extremely large request payloads."""
        # Create a very large payload
        large_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",  # pragma: allowlist secret
            "name": "A" * 10000,  # Very large name
            "extra_data": "X" * 100000,  # Very large extra field
        }

        response = test_client.post("/api/v1/auth/register", json=large_data)

        # Should reject gracefully
        assert response.status_code in [400, 413, 422]

    def test_null_and_empty_values(self, test_client):
        """Test handling of null and empty values."""
        test_cases = [
            {"email": None, "password": "test"},  # pragma: allowlist secret
            {"email": "", "password": "test"},  # pragma: allowlist secret
            {"email": "test@example.com", "password": None},
            {"email": "test@example.com", "password": ""},
            {"email": None, "password": None},
            {},  # Empty object
        ]

        for test_case in test_cases:
            response = test_client.post("/api/v1/auth/login", json=test_case)

            # Should return validation error
            assert response.status_code in [400, 422]


@pytest.mark.edge_cases
class TestDataCorruption:
    """Test handling of data corruption scenarios."""

    def test_corrupted_jwt_token(self, test_client):
        """Test handling of corrupted JWT tokens."""
        corrupted_tokens = [
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.corrupted.signature",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..signature",  # Empty payload
            "header.payload.",  # Missing signature
            "....",  # Multiple dots
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Incomplete token
        ]

        for token in corrupted_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = test_client.get("/api/v1/profile/me", headers=headers)

            # Should return 401 Unauthorized
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_database_constraint_violations(self, test_db_session, unique_user_factory):
        """Test handling of database constraint violations."""
        from src.entities.account import Account
        from src.libs.password import create_password_hash

        user_data = unique_user_factory("constraint")
        password_hash, salt = create_password_hash(user_data["password"])

        # Create first account
        account1 = Account(
            name=user_data["name"],
            email=user_data["email"],
            password=password_hash,
            password_salt=salt,
            status="ACTIVE",
        )
        test_db_session.add(account1)
        test_db_session.commit()

        # Try to create duplicate account (should violate unique constraint)
        account2 = Account(
            name=user_data["name"] + "2",
            email=user_data["email"],  # Same email
            password=password_hash,
            password_salt=salt,
            status="ACTIVE",
        )
        test_db_session.add(account2)

        # Should raise integrity error
        with pytest.raises((IntegrityError, Exception)):  # Could be IntegrityError or similar
            test_db_session.commit()


@pytest.mark.edge_cases
class TestNetworkFailureSimulation:
    """Test network failure simulation scenarios."""

    @patch("src.dependencies.redis.get_redis_client")
    def test_redis_connection_failure(self, mock_get_redis, test_client, created_test_user):
        """Test handling of Redis connection failures."""
        # Mock Redis connection failure
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Redis connection failed")
        mock_get_redis.return_value = mock_redis

        # Login should still work (graceful degradation)
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": created_test_user["email"], "password": created_test_user["password"], "remember_me": False},
        )

        # Should either succeed (if Redis is optional) or fail gracefully
        assert response.status_code in [200, 500, 503]

    @patch("src.extensions.ext_db.db_engine.get_engine")
    def test_database_connection_failure(self, mock_get_engine, test_client):
        """Test handling of database connection failures."""
        # Mock database engine failure
        mock_get_engine.side_effect = RuntimeError("Database connection failed")

        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password",  # pragma: allowlist secret
                "remember_me": False,  # pragma: allowlist secret
            },  # pragma: allowlist secret
        )

        # Should return 500 Internal Server Error or 503 Service Unavailable
        assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE]

    def test_slow_network_conditions(self, test_client, created_test_user):
        """Test behavior under slow network conditions."""
        # Simulate slow network by adding delays
        original_post = test_client.post

        def slow_post(*args, **kwargs):
            time.sleep(0.1)  # Add 100ms delay
            return original_post(*args, **kwargs)

        test_client.post = slow_post

        start_time = time.time()
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": created_test_user["email"], "password": created_test_user["password"], "remember_me": False},
        )
        end_time = time.time()

        # Should still complete successfully
        assert response.status_code in [200, 408]  # 408 = Request Timeout

        # Should take at least the delay time
        assert end_time - start_time >= 0.1


@pytest.mark.edge_cases
class TestTimingAttacks:
    """Test protection against timing attacks."""

    def test_login_timing_consistency(self, test_client, created_test_user):
        """Test that login timing is consistent for valid vs invalid users."""
        valid_login = {
            "email": created_test_user["email"],
            "password": created_test_user["password"],
            "remember_me": False,
        }

        invalid_user_login = {
            "email": "nonexistent@example.com",
            "password": "any_password",  # pragma: allowlist secret
            "remember_me": False,  # pragma: allowlist secret
        }  # pragma: allowlist secret

        invalid_password_login = {
            "email": created_test_user["email"],
            "password": "wrong_password",  # pragma: allowlist secret
            "remember_me": False,
        }

        # Measure timing for different scenarios
        def measure_login_time(login_data):
            start_time = time.time()
            test_client.post("/api/v1/auth/login", json=login_data)
            return time.time() - start_time

        # Warm up
        for _ in range(3):
            measure_login_time(valid_login)

        # Measure actual times
        valid_times = [measure_login_time(valid_login) for _ in range(5)]
        invalid_user_times = [measure_login_time(invalid_user_login) for _ in range(5)]
        invalid_pass_times = [measure_login_time(invalid_password_login) for _ in range(5)]

        # Calculate averages
        avg_valid = sum(valid_times) / len(valid_times)
        avg_invalid_user = sum(invalid_user_times) / len(invalid_user_times)
        avg_invalid_pass = sum(invalid_pass_times) / len(invalid_pass_times)

        # Timing differences should not be too significant (within 50ms)
        max_diff = max(abs(avg_valid - avg_invalid_user), abs(avg_valid - avg_invalid_pass))
        assert max_diff < 0.05, f"Timing difference {max_diff:.3f}s may allow timing attacks"
