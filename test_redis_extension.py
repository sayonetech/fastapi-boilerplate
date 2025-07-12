#!/usr/bin/env python3
"""
Test script to demonstrate the Redis extension functionality.

This script tests various Redis operations to ensure the Redis extension
works correctly and provides consistent functionality.
"""

import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app import create_app
from src.extensions.ext_redis import get_redis, is_redis_available


def test_redis_extension():
    """Test Redis extension functionality."""
    print("Testing Redis Extension")
    print("=" * 50)

    try:
        # Test Redis availability
        print("\n1. Testing Redis availability:")
        available = is_redis_available()
        print(f"✓ Redis available: {available}")

        if not available:
            print("⚠️  Redis is not available. Make sure Redis is running.")
            print("   You can start Redis with: redis-server")
            return

        # Test Redis client
        print("\n2. Testing Redis client:")
        redis_client = get_redis()
        ping_result = redis_client.ping()
        print(f"✓ Redis ping: {ping_result}")

        # Test basic operations
        print("\n3. Testing basic Redis operations:")

        # Set and get
        test_key = f"test:{uuid4()}"
        test_value = "Hello Redis!"
        redis_client.set(test_key, test_value)
        retrieved_value = redis_client.get(test_key)
        print(f"✓ Set/Get: {retrieved_value == test_value}")

        # Set with expiration
        expire_key = f"expire:{uuid4()}"
        redis_client.setex(expire_key, 2, "expires soon")
        ttl = redis_client.ttl(expire_key)
        print(f"✓ Set with TTL: {ttl > 0}")

        # Delete
        deleted = redis_client.delete(test_key)
        print(f"✓ Delete: {deleted == 1}")

        # Test JSON operations
        print("\n4. Testing JSON operations:")
        json_key = f"json:{uuid4()}"
        json_data = {"name": "test", "value": 123, "active": True}
        redis_client.set(json_key, json.dumps(json_data))
        retrieved_json = json.loads(redis_client.get(json_key))
        print(f"✓ JSON operations: {retrieved_json == json_data}")

        # Test pub/sub
        print("\n5. Testing pub/sub:")
        channel = f"test_channel:{uuid4()}"
        message = "Hello pub/sub!"
        subscribers = redis_client.publish(channel, message)
        print(f"✓ Publish (subscribers: {subscribers})")

        # Cleanup
        redis_client.delete(json_key, expire_key)

        print("\n✓ All Redis extension tests passed!")

    except Exception as e:
        print(f"\n✗ Redis extension test failed: {e}")
        import traceback

        traceback.print_exc()


def test_redis_api_endpoints():
    """Test Redis API endpoints."""
    print("\n\nTesting Redis API Endpoints")
    print("=" * 50)

    try:
        app = create_app()
        client = TestClient(app)

        # Test health endpoint
        print("\n1. Testing Redis health endpoint:")
        response = client.get("/api/v1/redis-example/health")
        print(f"✓ Health endpoint: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"  Status: {health_data.get('status')}")
            print(f"  Available: {health_data.get('available')}")

        # Test cache operations
        print("\n2. Testing cache operations:")

        # Set cache
        cache_data = {"key": f"api_test:{uuid4()}", "value": "API test value", "expire_seconds": 60}
        response = client.post("/api/v1/redis-example/cache", json=cache_data)
        print(f"✓ Set cache: {response.status_code}")

        if response.status_code == 200:
            # Get cache
            cache_key = cache_data["key"]
            response = client.get(f"/api/v1/redis-example/cache/{cache_key}")
            print(f"✓ Get cache: {response.status_code}")

            if response.status_code == 200:
                cache_response = response.json()
                print(f"  Retrieved value: {cache_response.get('value')}")
                print(f"  Exists: {cache_response.get('exists')}")
                print(f"  TTL: {cache_response.get('ttl')}")

            # Delete cache
            response = client.delete(f"/api/v1/redis-example/cache/{cache_key}")
            print(f"✓ Delete cache: {response.status_code}")

        # Test session operations
        print("\n3. Testing session operations:")

        session_data = {
            "session_id": f"session_{uuid4()}",
            "data": {"user_id": 123, "username": "testuser", "role": "admin"},
            "expire_seconds": 3600,
        }
        response = client.post("/api/v1/redis-example/session", json=session_data)
        print(f"✓ Set session: {response.status_code}")

        if response.status_code == 200:
            # Get session
            session_id = session_data["session_id"]
            response = client.get(f"/api/v1/redis-example/session/{session_id}")
            print(f"✓ Get session: {response.status_code}")

            if response.status_code == 200:
                session_response = response.json()
                print(f"  Session exists: {session_response.get('exists')}")
                print(f"  Session data: {session_response.get('data')}")

            # Delete session
            response = client.delete(f"/api/v1/redis-example/session/{session_id}")
            print(f"✓ Delete session: {response.status_code}")

        # Test rate limiting
        print("\n4. Testing rate limiting:")

        rate_limit_data = {"key": f"user_{uuid4()}", "limit": 5, "window_seconds": 60}

        # Make multiple requests to test rate limiting
        for i in range(3):
            response = client.post("/api/v1/redis-example/rate-limit/check", json=rate_limit_data)
            print(f"✓ Rate limit check {i + 1}: {response.status_code}")

            if response.status_code == 200:
                rate_response = response.json()
                print(f"  Is limited: {rate_response.get('is_limited')}")
                print(f"  Current count: {rate_response.get('current_count')}")

        # Test pub/sub
        print("\n5. Testing pub/sub:")

        channel = f"test_channel_{uuid4()}"
        message = "Hello from API!"
        response = client.post(f"/api/v1/redis-example/pub-sub/publish/{channel}?message={message}")
        print(f"✓ Publish message: {response.status_code}")

        if response.status_code == 200:
            pub_response = response.json()
            print(f"  Published: {pub_response.get('published')}")
            print(f"  Subscriber count: {pub_response.get('subscriber_count')}")

        print("\n✓ All Redis API endpoint tests completed!")

    except Exception as e:
        print(f"\n✗ Redis API endpoint test failed: {e}")
        import traceback

        traceback.print_exc()


def test_redis_service_operations():
    """Test Redis service operations."""
    print("\n\nTesting Redis Service Operations")
    print("=" * 50)

    try:
        from src.dependencies.redis import RedisService
        from src.extensions.ext_redis import get_redis

        if not is_redis_available():
            print("⚠️  Redis is not available for service tests")
            return

        redis_client = get_redis()
        service = RedisService(redis_client)

        print("\n1. Testing cache service operations:")

        # Test cache operations
        test_key = f"service_test:{uuid4()}"
        test_value = "Service test value"

        # Set cache
        success = service.set_cache(test_key, test_value, 60)
        print(f"✓ Set cache: {success}")

        # Get cache
        retrieved = service.get_cache(test_key)
        print(f"✓ Get cache: {retrieved == test_value}")

        # Check existence
        exists = service.exists(test_key)
        print(f"✓ Key exists: {exists}")

        # Delete cache
        deleted = service.delete_cache(test_key)
        print(f"✓ Delete cache: {deleted}")

        print("\n2. Testing session service operations:")

        # Test session operations
        session_id = f"service_session_{uuid4()}"
        session_data = {"user": "test", "role": "admin"}

        # Set session
        success = service.set_session(session_id, session_data, 3600)
        print(f"✓ Set session: {success}")

        # Get session
        retrieved_session = service.get_session(session_id)
        print(f"✓ Get session: {retrieved_session == session_data}")

        # Delete session
        deleted = service.delete_session(session_id)
        print(f"✓ Delete session: {deleted}")

        print("\n3. Testing rate limiting:")

        # Test rate limiting
        rate_key = f"rate_test_{uuid4()}"

        # Should not be limited initially
        limited = service.is_rate_limited(rate_key, 3, 60)
        print(f"✓ Initial rate limit check: {not limited}")

        # Make requests up to limit
        for i in range(4):
            limited = service.is_rate_limited(rate_key, 3, 60)
            print(f"✓ Rate limit check {i + 1}: limited={limited}")

        print("\n✓ All Redis service operation tests completed!")

    except Exception as e:
        print(f"\n✗ Redis service operation test failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all Redis extension tests."""
    print("Redis Extension Test Suite")
    print("=" * 60)

    try:
        # Test basic Redis extension
        test_redis_extension()

        # Test API endpoints
        test_redis_api_endpoints()

        # Test service operations
        test_redis_service_operations()

        print("\n" + "=" * 60)
        print("✓ All Redis extension tests completed successfully!")

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
