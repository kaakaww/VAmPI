"""
Health Check Tests

These tests verify that the VAmPI API is accessible and properly configured
before running the vulnerability tests. They should run first (hence test_00_).
"""

import pytest
import requests


def test_api_is_accessible(api_base_url: str):
    """
    Verify that the VAmPI API is accessible.

    This is a sanity check to ensure the API is running before attempting
    to run vulnerability tests.
    """
    try:
        response = requests.get(f"{api_base_url}/", timeout=5)
        assert response.status_code == 200, \
            f"API returned status {response.status_code}, expected 200"
        print(f"\n✓ VAmPI API is accessible at {api_base_url}")
    except requests.exceptions.ConnectionError:
        pytest.fail(f"Cannot connect to VAmPI API at {api_base_url}. Is the API running?")
    except requests.exceptions.Timeout:
        pytest.fail(f"Connection to {api_base_url} timed out. Is the API running?")


def test_default_users_exist(api_base_url: str, default_credentials: dict):
    """
    Verify that the default bootstrap users exist.

    This ensures the database has been properly initialized with the
    expected test users (admin, name1, name2).
    """
    for user_key, creds in default_credentials.items():
        username = creds["username"]
        password = creds["password"]

        response = requests.post(
            f"{api_base_url}/users/v1/login",
            json={"username": username, "password": password},
            timeout=5
        )

        assert response.status_code == 200, \
            f"Default user '{username}' cannot login. Expected 200, got {response.status_code}"

        data = response.json()
        assert data.get("status") == "success", \
            f"Login for '{username}' did not succeed: {data}"

        assert data.get("auth_token"), \
            f"No auth token returned for '{username}'"

    print(f"\n✓ All default users (admin, name1, name2) are accessible")


def test_bootstrap_data_exists(api_base_url: str, admin_token: str):
    """
    Verify that bootstrap data exists (users beyond the defaults).

    This checks that the database has been populated with more than just
    the 3 default users, indicating successful bootstrap.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(
        f"{api_base_url}/users/v1",
        headers=headers,
        timeout=5
    )

    assert response.status_code == 200, \
        f"Cannot access users list. Expected 200, got {response.status_code}"

    data = response.json()
    users = data.get("users", [])

    # Should have at least the 3 default users, but likely many more from bootstrap
    assert len(users) >= 3, \
        f"Expected at least 3 users, found {len(users)}. Database may not be initialized."

    if len(users) > 10:
        print(f"\n✓ Bootstrap data present: {len(users)} users found")
    else:
        print(f"\n⚠ Warning: Only {len(users)} users found. Expected 50+ from bootstrap.")


def test_vulnerable_mode_is_enabled(api_base_url: str):
    """
    Verify that VAmPI is running in vulnerable mode.

    The tests are designed to pass when vulnerable=1. This test verifies
    the configuration by checking for a known vulnerability indicator.
    """
    # Test the debug endpoint which should be accessible in vulnerable mode
    response = requests.get(f"{api_base_url}/users/v1/_debug", timeout=5)

    assert response.status_code == 200, \
        f"Debug endpoint not accessible. Is vulnerable=1? Got status {response.status_code}"

    data = response.json()
    users = data.get("users", [])

    # Check if passwords are exposed (vulnerability indicator)
    has_passwords = any("password" in user for user in users)

    assert has_passwords, \
        "Debug endpoint does not expose passwords. Is vulnerable=1?"

    print(f"\n✓ VAmPI is running in vulnerable mode (vulnerable=1)")
    print(f"  - Debug endpoint accessible: ✓")
    print(f"  - Passwords exposed: ✓")


def test_jwt_token_generation_works(api_base_url: str, user1_token: str):
    """
    Verify that JWT token generation and validation works.

    This ensures that the authentication system is functional before
    running tests that depend on it.
    """
    # Try to access a protected endpoint with the token
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = requests.get(
        f"{api_base_url}/me",
        headers=headers,
        timeout=5
    )

    assert response.status_code == 200, \
        f"Cannot access protected endpoint with token. Expected 200, got {response.status_code}"

    data = response.json()
    assert data.get("status") == "success", \
        f"Token validation failed: {data}"

    user_data = data.get("data", {})
    assert user_data.get("username") == "name1", \
        f"Token does not match expected user. Got {user_data.get('username')}"

    print(f"\n✓ JWT token generation and validation working")
