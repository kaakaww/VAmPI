"""
Test User and Password Enumeration Vulnerability (API2:2023 Broken Authentication)

This test demonstrates username and password enumeration vulnerability in the
POST /users/v1/login endpoint. When vuln=1, the endpoint returns different error
messages for invalid usernames vs invalid passwords, allowing attackers to
enumerate valid usernames in the system.

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/

Vulnerability Location: api_views/users.py:101-110
"""

import pytest
import requests
import uuid


def test_user_enumeration_valid_username_wrong_password(api_base_url: str, default_credentials: dict):
    """
    Test user enumeration by attempting login with valid username and wrong password.

    When vuln=1, the API returns a specific error message:
    "Password is not correct for the given username."

    This error message confirms that the username exists, allowing an attacker
    to enumerate valid usernames.

    Expected behavior when vuln=1:
        - Returns specific error: "Password is not correct for the given username."
        - Confirms username exists

    Expected behavior when vuln=0:
        - Returns generic error: "Username or Password Incorrect!"
        - Does not reveal whether username exists
    """
    valid_username = default_credentials["admin"]["username"]
    wrong_password = "definitelywrongpassword123"

    response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": valid_username, "password": wrong_password}
    )

    # Should return 200 with error message (not 401)
    assert response.status_code == 200, \
        f"Unexpected status code. Expected 200, got {response.status_code}"

    data = response.json()
    error_message = data.get("message", "")

    # When vulnerable, this should say "Password is not correct for the given username."
    # When secure, it should say "Username or Password Incorrect!"
    assert "Password is not correct" in error_message or "password" in error_message.lower(), \
        f"User enumeration vulnerability appears patched. Error message does not reveal password is wrong. " \
        f"Got: '{error_message}'"

    # The vulnerable message specifically mentions "for the given username"
    assert "given username" in error_message.lower() or "username" in error_message.lower(), \
        f"Error message does not confirm username exists: '{error_message}'"


def test_user_enumeration_invalid_username(api_base_url: str):
    """
    Test user enumeration by attempting login with invalid username.

    When vuln=1, the API returns a specific error message:
    "Username does not exist"

    This explicitly confirms that the username does NOT exist, allowing an
    attacker to enumerate valid vs invalid usernames.

    Expected behavior when vuln=1:
        - Returns specific error: "Username does not exist"
        - Explicitly reveals username doesn't exist

    Expected behavior when vuln=0:
        - Returns generic error: "Username or Password Incorrect!"
        - Does not reveal whether username exists or not
    """
    invalid_username = f"nonexistent_user_{uuid.uuid4().hex}"
    any_password = "anypassword123"

    response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": invalid_username, "password": any_password}
    )

    assert response.status_code == 200, \
        f"Unexpected status code. Expected 200, got {response.status_code}"

    data = response.json()
    error_message = data.get("message", "")

    # When vulnerable, this should explicitly say "Username does not exist"
    # When secure, it should say "Username or Password Incorrect!"
    assert "does not exist" in error_message.lower() or "not exist" in error_message.lower(), \
        f"User enumeration vulnerability appears patched. Error message does not reveal username validity. " \
        f"Got: '{error_message}'"


def test_user_enumeration_timing_attack(api_base_url: str, default_credentials: dict):
    """
    Test for timing-based user enumeration.

    Even with generic error messages, timing differences in response times can
    reveal whether a username exists:
    - Valid username: Password hash verification takes time
    - Invalid username: Fast response (no password check needed)

    This test measures response times to detect timing-based enumeration.

    Note: This is more subtle than message-based enumeration and may not be
    exploitable in all scenarios (depends on network latency, server load, etc.)

    Expected behavior when vuln=1:
        - Message-based enumeration works, so timing is less relevant
        - But timing differences may still exist

    Expected behavior when vuln=0:
        - Messages are generic, but timing may still leak information
        - This is a more subtle vulnerability
    """
    import time

    valid_username = default_credentials["admin"]["username"]
    invalid_username = f"fake_{uuid.uuid4().hex}"
    wrong_password = "wrongpassword"

    # Test with valid username (should take longer due to password verification)
    start_valid = time.time()
    response_valid = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": valid_username, "password": wrong_password}
    )
    time_valid = time.time() - start_valid

    # Test with invalid username (should be faster)
    start_invalid = time.time()
    response_invalid = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": invalid_username, "password": wrong_password}
    )
    time_invalid = time.time() - start_invalid

    # Note: Timing attacks are unreliable in integration tests due to network variance
    # This test is mostly for documentation/awareness purposes
    # In real scenarios, an attacker would make many requests and average the times

    print(f"Valid username timing: {time_valid:.4f}s")
    print(f"Invalid username timing: {time_invalid:.4f}s")
    print(f"Timing difference: {abs(time_valid - time_invalid):.4f}s")

    # We don't assert on timing differences because they're unreliable in tests
    # But we document that this is a potential attack vector


def test_user_enumeration_enumerate_multiple_users(api_base_url: str, default_credentials: dict):
    """
    Test systematic username enumeration using the different error messages.

    This demonstrates how an attacker can build a list of valid usernames
    by testing common usernames and observing the error messages.

    Steps:
        1. Test a list of common usernames
        2. Classify each as valid or invalid based on error message
        3. Prove that we can accurately enumerate real users

    Expected behavior when vuln=1:
        - Can accurately identify which usernames exist
        - Different error messages enable enumeration

    Expected behavior when vuln=0:
        - Cannot distinguish valid from invalid usernames
        - Generic error messages prevent enumeration
    """
    # List of usernames to test (including known valid ones)
    test_usernames = [
        "admin",  # Known valid
        "name1",  # Known valid
        "name2",  # Known valid
        "root",   # Likely invalid
        "administrator",  # Likely invalid
        "user",   # Likely invalid
        f"fake_{uuid.uuid4().hex[:4]}",  # Definitely invalid
    ]

    wrong_password = "testpassword123"
    results = {
        "exists": [],
        "does_not_exist": [],
        "unknown": []
    }

    for username in test_usernames:
        response = requests.post(
            f"{api_base_url}/users/v1/login",
            json={"username": username, "password": wrong_password}
        )

        if response.status_code == 200:
            data = response.json()
            message = data.get("message", "").lower()

            if "password is not correct" in message or "password" in message:
                results["exists"].append(username)
            elif "does not exist" in message or "not exist" in message:
                results["does_not_exist"].append(username)
            else:
                results["unknown"].append(username)

    # When vulnerable, we should be able to identify the known valid users
    known_valid_users = ["admin", "name1", "name2"]

    for user in known_valid_users:
        assert user in results["exists"], \
            f"Failed to enumerate known user '{user}'. " \
            f"Enumeration results: {results}"

    # And we should identify at least some invalid users
    assert len(results["does_not_exist"]) > 0, \
        "No invalid usernames detected - enumeration may not be working"


def test_successful_login_returns_different_response(api_base_url: str, default_credentials: dict):
    """
    Control test: Verify that successful logins return different responses than failed ones.

    This establishes the baseline behavior for successful authentication,
    which should be different from the error cases.

    Expected behavior (both vuln=1 and vuln=0):
        - Successful login returns 200 with status "success"
        - Includes an auth_token
        - Message says "Successfully logged in."
    """
    valid_creds = default_credentials["admin"]

    response = requests.post(
        f"{api_base_url}/users/v1/login",
        json={
            "username": valid_creds["username"],
            "password": valid_creds["password"]
        }
    )

    assert response.status_code == 200, \
        "Successful login failed - API may be broken"

    data = response.json()
    assert data.get("status") == "success", \
        f"Successful login should return status 'success', got '{data.get('status')}'"

    assert data.get("auth_token") is not None, \
        "Successful login should return an auth_token"

    assert "success" in data.get("message", "").lower(), \
        "Successful login message should indicate success"


def test_generic_error_message_comparison(api_base_url: str, default_credentials: dict):
    """
    Test that demonstrates the difference between vulnerable and secure error messages.

    This test explicitly shows what the error messages look like in both scenarios
    to document the vulnerability clearly.

    Expected messages when vuln=1:
        - Valid username + wrong password: "Password is not correct for the given username."
        - Invalid username: "Username does not exist"

    Expected messages when vuln=0:
        - Both cases: "Username or Password Incorrect!"
    """
    valid_username = default_credentials["admin"]["username"]
    invalid_username = f"fake_{uuid.uuid4().hex}"
    wrong_password = "wrong"

    # Test 1: Valid username, wrong password
    response1 = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": valid_username, "password": wrong_password}
    )
    message1 = response1.json().get("message", "")

    # Test 2: Invalid username
    response2 = requests.post(
        f"{api_base_url}/users/v1/login",
        json={"username": invalid_username, "password": wrong_password}
    )
    message2 = response2.json().get("message", "")

    print(f"\nError message for valid username + wrong password: '{message1}'")
    print(f"Error message for invalid username: '{message2}'")

    # When vulnerable, these messages should be DIFFERENT
    # When secure, these messages should be the SAME
    assert message1 != message2, \
        f"User enumeration appears patched - error messages are identical: '{message1}'"

    # The different messages enable user enumeration
    assert "password" in message1.lower() and "username" in message2.lower(), \
        "Error messages do not follow the expected vulnerable pattern"
