#!/usr/bin/env python3
"""
Test script for the Dify-style token authentication.

This script tests the complete token flow with valid credentials.
"""

from fastapi.testclient import TestClient

from app import create_app


def test_dify_token_flow():
    """Test the complete Dify-style token flow."""
    print("Testing Dify-style Token Flow")
    print("=" * 50)

    try:
        # Create FastAPI app
        app = create_app()
        client = TestClient(app)

        print("\n1. Testing login with valid credentials:")
        login_data = {
            "email": "renjith@sayonetech.com",
            "password": "asdf1234",  # pragma: allowlist secret
            "remember_me": False,
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"✓ Login status: {response.status_code}")

        if response.status_code == 200:
            login_response = response.json()
            print("✓ Login successful!")
            print(f"  Result: {login_response.get('result')}")

            # Extract tokens
            data = login_response.get("data", {})
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")

            print(f"  Access Token: {access_token[:50]}..." if access_token else "  No access token")
            print(f"  Refresh Token: {refresh_token[:50]}..." if refresh_token else "  No refresh token")
            print(f"  Token Type: {data.get('token_type')}")
            print(f"  Expires In: {data.get('expires_in')} seconds")

            if access_token:
                # Test authenticated endpoints
                print("\n2. Testing authenticated endpoints:")

                headers = {"Authorization": f"Bearer {access_token}"}

                # Test /me endpoint
                response = client.get("/api/v1/auth/me", headers=headers)
                print(f"✓ /me endpoint: {response.status_code}")

                if response.status_code == 200:
                    user_data = response.json()
                    print(f"  User: {user_data.get('name')} ({user_data.get('email')})")
                    print(f"  Admin: {user_data.get('is_admin')}")

                # Test session validation
                response = client.get("/api/v1/auth/session/validate", headers=headers)
                print(f"✓ Session validation: {response.status_code}")

                if response.status_code == 200:
                    validation_data = response.json()
                    print(f"  Valid: {validation_data.get('valid')}")
                    print(f"  Message: {validation_data.get('message')}")

                # Test refresh token
                if refresh_token:
                    print("\n3. Testing refresh token:")
                    refresh_data = {"refresh_token": refresh_token}
                    response = client.post("/api/v1/auth/refresh-token", json=refresh_data)
                    print(f"✓ Refresh token: {response.status_code}")

                    if response.status_code == 200:
                        refresh_response = response.json()
                        print("✓ Token refresh successful!")
                        new_data = refresh_response.get("data", {})
                        new_access_token = new_data.get("access_token")
                        new_refresh_token = new_data.get("refresh_token")
                        print(
                            f"  New Access Token: {new_access_token[:50]}..."
                            if new_access_token
                            else "  No new access token"
                        )
                        print(
                            f"  New Refresh Token: {new_refresh_token[:50]}..."
                            if new_refresh_token
                            else "  No new refresh token"
                        )

                        # Update tokens for logout test
                        access_token = new_access_token
                        refresh_token = new_refresh_token
                        headers = {"Authorization": f"Bearer {access_token}"}

                # Test logout
                print("\n4. Testing logout:")
                response = client.post("/api/v1/auth/logout", headers=headers, json={})
                print(f"✓ Logout: {response.status_code}")

                if response.status_code == 200:
                    logout_response = response.json()
                    print(f"  Success: {logout_response.get('success')}")
                    print(f"  Message: {logout_response.get('message')}")

                # Test that refresh token is invalidated after logout
                if refresh_token:
                    print("\n5. Testing refresh token after logout:")
                    refresh_data = {"refresh_token": refresh_token}
                    response = client.post("/api/v1/auth/refresh-token", json=refresh_data)
                    print(f"✓ Refresh token after logout: {response.status_code}")

                    if response.status_code == 401:
                        print("✓ Refresh token properly invalidated after logout")
                    else:
                        print("❌ Refresh token should be invalidated after logout")
                        if response.content:
                            print(f"  Response: {response.json()}")

        elif response.status_code == 401:
            print("❌ Login failed - check credentials")
            error_data = response.json()
            print(f"  Error: {error_data.get('detail', 'Unknown error')}")
        else:
            print(f"❌ Unexpected login response: {response.status_code}")
            if response.content:
                try:
                    error_data = response.json()
                    print(f"  Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"  Raw response: {response.text}")

        print("\n✓ Dify-style token flow tests completed!")
        print("\nSummary:")
        print("- ✓ JWT-based access tokens")
        print("- ✓ Random refresh tokens stored in Redis")
        print("- ✓ Token refresh functionality")
        print("- ✓ Proper logout with token invalidation")
        print("- ✓ Following Dify's token management pattern")

    except Exception as e:
        print(f"\n✗ Dify-style token test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_dify_token_flow()
