"""
Shared pytest fixtures for VAmPI integration tests.

These fixtures provide common setup and utilities for testing the VAmPI API,
including authentication tokens, API base URL configuration, and test helpers.
"""

import os
import pytest
import requests
from typing import Dict, Optional


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Get the VAmPI API base URL from environment or use default.

    Returns:
        str: Base URL for the VAmPI API (e.g., 'http://vampi:5000' or 'http://localhost:5000')
    """
    return os.environ.get("VAMPI_BASE_URL", "http://localhost:5000")


@pytest.fixture(scope="session")
def default_credentials() -> Dict[str, Dict[str, str]]:
    """
    Default test credentials created by bootstrap.

    Returns:
        dict: Dictionary of username -> {username, password} mappings
    """
    return {
        "admin": {"username": "admin", "password": "pass1"},
        "user1": {"username": "name1", "password": "pass1"},
        "user2": {"username": "name2", "password": "pass2"},
    }


def login_and_get_token(api_base_url: str, username: str, password: str) -> Optional[str]:
    """
    Helper function to login and retrieve an auth token.

    Args:
        api_base_url: Base URL of the API
        username: Username to login with
        password: Password to login with

    Returns:
        str: JWT auth token, or None if login failed
    """
    try:
        response = requests.post(
            f"{api_base_url}/users/v1/login",
            json={"username": username, "password": password},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("auth_token")

    except requests.exceptions.RequestException as e:
        print(f"Login failed for {username}: {e}")

    return None


@pytest.fixture(scope="function")
def admin_token(api_base_url: str, default_credentials: Dict) -> str:
    """
    Get a valid admin auth token.

    Args:
        api_base_url: Base URL from api_base_url fixture
        default_credentials: Default credentials from default_credentials fixture

    Returns:
        str: Valid JWT token for the admin user
    """
    creds = default_credentials["admin"]
    token = login_and_get_token(api_base_url, creds["username"], creds["password"])
    assert token is not None, "Failed to obtain admin token"
    return token


@pytest.fixture(scope="function")
def user1_token(api_base_url: str, default_credentials: Dict) -> str:
    """
    Get a valid auth token for user1 (name1).

    Args:
        api_base_url: Base URL from api_base_url fixture
        default_credentials: Default credentials from default_credentials fixture

    Returns:
        str: Valid JWT token for user1
    """
    creds = default_credentials["user1"]
    token = login_and_get_token(api_base_url, creds["username"], creds["password"])
    assert token is not None, "Failed to obtain user1 token"
    return token


@pytest.fixture(scope="function")
def user2_token(api_base_url: str, default_credentials: Dict) -> str:
    """
    Get a valid auth token for user2 (name2).

    Args:
        api_base_url: Base URL from api_base_url fixture
        default_credentials: Default credentials from default_credentials fixture

    Returns:
        str: Valid JWT token for user2
    """
    creds = default_credentials["user2"]
    token = login_and_get_token(api_base_url, creds["username"], creds["password"])
    assert token is not None, "Failed to obtain user2 token"
    return token


@pytest.fixture(scope="function")
def auth_headers(user1_token: str) -> Dict[str, str]:
    """
    Get authorization headers for authenticated requests.

    Args:
        user1_token: JWT token from user1_token fixture

    Returns:
        dict: Headers dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {user1_token}"}


@pytest.fixture(scope="session")
def get_user_books(api_base_url: str):
    """
    Factory fixture to get books for a specific user.

    Returns:
        function: A function that takes (username, token) and returns list of books
    """
    def _get_books(username: str, token: str) -> list:
        """
        Get all books for a user.

        Args:
            username: Username to get books for
            token: Valid auth token

        Returns:
            list: List of book dictionaries
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{api_base_url}/books/v1", headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data.get("Books", [])

        return []

    return _get_books
