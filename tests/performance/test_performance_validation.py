"""
Performance validation tests for the authentication system.

These tests validate performance characteristics including:
- Response time benchmarks
- Concurrent user handling
- Rate limiting performance
- Memory usage validation
- Database query optimization
"""

import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest


@pytest.mark.performance
class TestAuthenticationPerformance:
    """Test authentication endpoint performance."""

    def test_login_response_time(self, test_client, created_test_user):
        """Test that login response time is within acceptable limits."""
        login_data = {
            "email": created_test_user["email"],
            "password": created_test_user["password"],
            "remember_me": False,
        }

        # Warm up
        test_client.post("/api/v1/auth/login", json=login_data)

        # Measure response times
        response_times = []
        for _ in range(10):
            start_time = time.time()
            response = test_client.post("/api/v1/auth/login", json=login_data)
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            # Each request should complete within reasonable time
            assert response_time < 2.0, f"Login took {response_time:.3f}s, which is too slow"

        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        # Performance assertions
        assert avg_time < 1.0, f"Average login time {avg_time:.3f}s exceeds 1 second"
        assert max_time < 2.0, f"Maximum login time {max_time:.3f}s exceeds 2 seconds"

    def test_registration_response_time(self, test_client, unique_user_factory):
        """Test that registration response time is within acceptable limits."""
        # Measure response times for registration
        response_times = []

        for i in range(5):  # Fewer iterations since each creates a new user
            user_data = unique_user_factory(f"perftest{i}")

            start_time = time.time()
            response = test_client.post("/api/v1/auth/register", json=user_data)
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            # Each request should complete within reasonable time
            assert response_time < 3.0, f"Registration took {response_time:.3f}s, which is too slow"

        # Calculate statistics
        avg_time = statistics.mean(response_times)

        # Performance assertions
        assert avg_time < 2.0, f"Average registration time {avg_time:.3f}s exceeds 2 seconds"

    def test_token_validation_performance(self, test_client, created_test_user):
        """Test that token validation is fast."""
        # Get a valid token
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={"email": created_test_user["email"], "password": created_test_user["password"], "remember_me": False},
        )

        if login_response.status_code != 200:
            pytest.skip("Cannot get valid token for performance test")

        token_data = login_response.json()
        access_token = token_data["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Measure token validation times
        response_times = []
        for _ in range(20):
            start_time = time.time()
            response = test_client.get("/api/v1/auth/me", headers=headers)
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            # Token validation should be very fast
            assert response_time < 0.5, f"Token validation took {response_time:.3f}s, which is too slow"

        avg_time = statistics.mean(response_times)
        assert avg_time < 0.2, f"Average token validation time {avg_time:.3f}s exceeds 0.2 seconds"


@pytest.mark.performance
class TestConcurrentUserHandling:
    """Test concurrent user handling performance."""

    def test_concurrent_login_attempts(self, test_client, created_test_user):
        """Test that the system can handle concurrent login attempts."""
        login_data = {
            "email": created_test_user["email"],
            "password": created_test_user["password"],
            "remember_me": False,
        }

        def make_login_request():
            """Make a single login request and return response time."""
            start_time = time.time()
            response = test_client.post("/api/v1/auth/login", json=login_data)
            end_time = time.time()
            return {"status_code": response.status_code, "response_time": end_time - start_time}

        # Test with 10 concurrent requests
        num_concurrent = 10
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_login_request) for _ in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]

        # All requests should complete successfully
        successful_requests = [r for r in results if r["status_code"] == 200]
        assert len(successful_requests) >= num_concurrent * 0.8, "Too many concurrent requests failed"

        # Response times should still be reasonable under load
        response_times = [r["response_time"] for r in successful_requests]
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        assert avg_time < 3.0, f"Average response time under load {avg_time:.3f}s is too high"
        assert max_time < 5.0, f"Maximum response time under load {max_time:.3f}s is too high"

    def test_concurrent_registration_attempts(self, test_client, unique_user_factory):
        """Test that the system can handle concurrent registration attempts."""

        def make_registration_request(user_id):
            """Make a single registration request and return response time."""
            user_data = unique_user_factory(f"concurrent{user_id}")

            start_time = time.time()
            response = test_client.post("/api/v1/auth/register", json=user_data)
            end_time = time.time()
            return {"status_code": response.status_code, "response_time": end_time - start_time, "user_id": user_id}

        # Test with 5 concurrent registrations
        num_concurrent = 5
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_registration_request, i) for i in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]

        # All requests should complete (either success or validation error)
        completed_requests = [r for r in results if r["status_code"] in [200, 201, 400, 422]]
        assert len(completed_requests) == num_concurrent, "Some concurrent requests failed unexpectedly"

        # Response times should be reasonable
        response_times = [r["response_time"] for r in completed_requests]
        avg_time = statistics.mean(response_times)

        assert avg_time < 5.0, f"Average registration time under load {avg_time:.3f}s is too high"


@pytest.mark.performance
class TestRateLimitingPerformance:
    """Test rate limiting performance characteristics."""

    @patch("src.configs.madcrow_config")
    def test_rate_limiting_overhead(self, mock_config, test_client, created_test_user):
        """Test that rate limiting doesn't add significant overhead."""
        mock_config.ENABLE_LOGIN_RATE_LIMITING = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 100  # High limit to avoid triggering

        login_data = {
            "email": created_test_user["email"],
            "password": created_test_user["password"],
            "remember_me": False,
        }

        with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
            mock_instance = mock_rate_limiter_class.return_value
            mock_instance.is_rate_limited.return_value = False
            mock_instance.get_time_until_reset.return_value = 300

            # Measure response times with rate limiting enabled
            response_times_with_rl = []
            for _ in range(10):
                start_time = time.time()
                response = test_client.post("/api/v1/auth/login", json=login_data)
                end_time = time.time()
                response_times_with_rl.append(end_time - start_time)

        # Disable rate limiting
        mock_config.ENABLE_LOGIN_RATE_LIMITING = False

        # Measure response times without rate limiting
        response_times_without_rl = []
        for _ in range(10):
            start_time = time.time()
            response = test_client.post("/api/v1/auth/login", json=login_data)
            end_time = time.time()
            response_times_without_rl.append(end_time - start_time)

        # Calculate overhead
        avg_with_rl = statistics.mean(response_times_with_rl)
        avg_without_rl = statistics.mean(response_times_without_rl)
        overhead = avg_with_rl - avg_without_rl

        # Rate limiting overhead should be minimal
        assert overhead < 0.1, f"Rate limiting adds {overhead:.3f}s overhead, which is too much"

    @patch("src.configs.madcrow_config")
    def test_rate_limiting_accuracy_under_load(self, mock_config, test_client, created_test_user):
        """Test that rate limiting remains accurate under concurrent load."""
        mock_config.ENABLE_LOGIN_RATE_LIMITING = True
        mock_config.LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 3

        login_data = {
            "email": created_test_user["email"],
            "password": "wrong_password",  # Use wrong password to trigger rate limiting  # pragma: allowlist secret
            "remember_me": False,
        }

        with patch("src.utils.rate_limiter.RateLimiter") as mock_rate_limiter_class:
            attempt_count = 0
            lock = threading.Lock()

            def mock_is_rate_limited(email, redis_client):
                with lock:
                    return attempt_count >= 3

            def mock_increment(email, redis_client):
                nonlocal attempt_count
                with lock:
                    attempt_count += 1

            mock_instance = mock_rate_limiter_class.return_value
            mock_instance.is_rate_limited.side_effect = mock_is_rate_limited
            mock_instance.increment_rate_limit.side_effect = mock_increment
            mock_instance.get_time_until_reset.return_value = 300

            def make_failed_login():
                return test_client.post("/api/v1/auth/login", json=login_data)

            # Make 10 concurrent failed login attempts
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_failed_login) for _ in range(10)]
                responses = [future.result() for future in as_completed(futures)]

            # Count rate limited responses
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            auth_failed_count = sum(1 for r in responses if r.status_code == 401)

            # Should have some rate limited responses after the limit is reached
            assert rate_limited_count > 0, "Rate limiting should trigger under concurrent load"
            assert auth_failed_count > 0, "Some requests should fail with auth error before rate limiting"


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage characteristics."""

    def test_memory_usage_during_load(self, test_client, unique_user_factory):
        """Test that memory usage remains reasonable during load testing."""
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many operations
        for i in range(50):
            user_data = unique_user_factory(f"memtest{i}")
            response = test_client.post("/api/v1/auth/register", json=user_data)

            # Also test login if registration succeeded
            if response.status_code in [200, 201]:
                test_client.post(
                    "/api/v1/auth/login",
                    json={"email": user_data["email"], "password": user_data["password"], "remember_me": False},
                )

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB, which may indicate a memory leak"

    def test_no_memory_leaks_in_token_operations(self, test_client, created_test_user):
        """Test that token operations don't cause memory leaks."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many token operations
        for _ in range(100):
            # Login to get token
            login_response = test_client.post(
                "/api/v1/auth/login",
                json={
                    "email": created_test_user["email"],
                    "password": created_test_user["password"],
                    "remember_me": False,
                },
            )

            if login_response.status_code == 200:
                token_data = login_response.json()
                access_token = token_data["data"]["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}

                # Use token
                test_client.get("/api/v1/auth/me", headers=headers)

                # Logout
                test_client.post("/api/v1/auth/logout", headers=headers)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be minimal for token operations
        assert memory_increase < 50, f"Token operations increased memory by {memory_increase:.2f}MB"


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database operation performance."""

    def test_user_lookup_performance(self, test_db_session, unique_user_factory):
        """Test that user lookup operations are fast."""
        from src.entities.account import Account
        from src.libs.password import create_password_hash

        # Create test users
        test_users = []
        for i in range(10):
            user_data = unique_user_factory(f"dbperf{i}")
            password_hash, salt = create_password_hash(user_data["password"])

            account = Account(
                name=user_data["name"],
                email=user_data["email"],
                password=password_hash,
                password_salt=salt,
                status="ACTIVE",
            )
            test_db_session.add(account)
            test_users.append(user_data)

        test_db_session.commit()

        # Test lookup performance
        lookup_times = []
        for user_data in test_users:
            start_time = time.time()
            account = Account.get_by_email(test_db_session, user_data["email"])
            end_time = time.time()

            lookup_time = end_time - start_time
            lookup_times.append(lookup_time)

            assert account is not None
            assert lookup_time < 0.1, f"User lookup took {lookup_time:.3f}s, which is too slow"

        avg_lookup_time = statistics.mean(lookup_times)
        assert avg_lookup_time < 0.05, f"Average user lookup time {avg_lookup_time:.3f}s is too slow"
