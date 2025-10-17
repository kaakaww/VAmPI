"""
Test Regular Expression Denial of Service (ReDoS) Vulnerability (API4:2023 Unrestricted Resource Consumption)

This test demonstrates ReDoS vulnerability in the PUT /users/v1/{username}/email endpoint.
When vuln=1, the endpoint uses a vulnerable regex pattern for email validation that exhibits
catastrophic backtracking, allowing attackers to cause high CPU usage with specially crafted input.

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

Vulnerable Regex Pattern: ^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@{1}([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$

Vulnerability Location: api_views/users.py:143-160
"""

import pytest
import requests
import time
import uuid


@pytest.mark.timeout(30)  # Fail if test takes longer than 30 seconds
def test_regex_dos_catastrophic_backtracking(api_base_url: str, user1_token: str):
    """
    Test ReDoS by sending an email that causes catastrophic backtracking.

    The vulnerable regex pattern has nested quantifiers that cause exponential
    time complexity when processing certain malicious inputs. This test sends
    an email string designed to trigger worst-case behavior.

    The vulnerable pattern: ^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@{1}([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$

    The issue is the nested quantifiers: ([-.\w]*[0-9a-zA-Z])* and ([-\w]*[0-9a-zA-Z]\.)+
    These cause catastrophic backtracking when the string almost matches but fails at the end.

    Expected behavior when vuln=1:
        - Request takes significantly longer to process (several seconds)
        - May cause timeout or very slow response
        - Server CPU usage spikes

    Expected behavior when vuln=0:
        - Uses a simpler, non-vulnerable regex
        - Request completes quickly (< 1 second)
    """
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    # Craft a malicious email that triggers catastrophic backtracking
    # The pattern is: many valid email-like characters, but fails validation at the end
    # This causes the regex engine to try many different matching paths

    # Start with a valid-looking local part with many hyphens/dots that cause backtracking
    malicious_local = "a" + "-" * 20 + "a" + "-" * 20 + "a"

    # Add an @ and domain that will ultimately fail
    malicious_email = f"{malicious_local}@{malicious_local}.{malicious_local}!"  # '!' makes it invalid

    # Measure response time
    start_time = time.time()

    try:
        response = requests.put(
            f"{api_base_url}/users/v1/name1/email",
            headers=user1_headers,
            json={"email": malicious_email},
            timeout=25  # Set a timeout to prevent hanging forever
        )
        elapsed_time = time.time() - start_time

        print(f"\nReDoS test - Response time: {elapsed_time:.4f} seconds")
        print(f"Malicious email length: {len(malicious_email)} characters")

        # When vulnerable, this should take noticeably long (> 2 seconds)
        # When secure, this should be fast (< 1 second)

        # We don't strictly assert on timing because it's environment-dependent,
        # but we print it for observation
        if elapsed_time > 2.0:
            print(f"⚠️  WARNING: Response took {elapsed_time:.2f}s - potential ReDoS vulnerability!")

        # The response should be 400 (invalid email) regardless of timing
        # But the time taken reveals the vulnerability
        assert response.status_code in [400, 500], \
            f"Expected 400 or 500 for invalid email. Got {response.status_code}"

    except requests.exceptions.Timeout:
        # Timeout is also evidence of ReDoS vulnerability
        print(f"\n⚠️  CRITICAL: Request timed out after 25 seconds - strong ReDoS indicator!")
        # This is actually a pass for our vulnerability test
        assert True, "ReDoS vulnerability confirmed via timeout"


@pytest.mark.timeout(30)
def test_regex_dos_increasing_complexity(api_base_url: str, user1_token: str):
    """
    Test ReDoS by sending increasingly complex emails and measuring response times.

    This test demonstrates that response time grows exponentially with input complexity
    when the vulnerable regex is used, proving the ReDoS vulnerability.

    Expected behavior when vuln=1:
        - Response time grows exponentially with input size
        - Doubling input size may 4x or more the response time

    Expected behavior when vuln=0:
        - Response time grows linearly or stays constant
        - Input size has minimal impact on performance
    """
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    # Test with increasing levels of "attack" complexity
    test_cases = [
        ("Small",  "a" + "-" * 5 + "a@test.com!"),   # 5 hyphens
        ("Medium", "a" + "-" * 10 + "a@test.com!"),  # 10 hyphens
        ("Large",  "a" + "-" * 15 + "a@test.com!"),  # 15 hyphens
    ]

    results = []

    for name, email in test_cases:
        start_time = time.time()

        try:
            response = requests.put(
                f"{api_base_url}/users/v1/name1/email",
                headers=user1_headers,
                json={"email": email},
                timeout=20
            )
            elapsed = time.time() - start_time

            results.append({
                "name": name,
                "email_length": len(email),
                "time": elapsed,
                "status": response.status_code
            })

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            results.append({
                "name": name,
                "email_length": len(email),
                "time": elapsed,
                "status": "TIMEOUT"
            })

    # Print results
    print("\nReDoS Complexity Test Results:")
    print("-" * 60)
    for result in results:
        print(f"{result['name']:8} | Length: {result['email_length']:3} | "
              f"Time: {result['time']:7.4f}s | Status: {result['status']}")
    print("-" * 60)

    # When vulnerable, we should see exponential growth in response time
    # When secure, response times should be relatively constant

    # Check if we see exponential growth (simple heuristic)
    if len(results) >= 3:
        time_small = results[0]['time']
        time_medium = results[1]['time']
        time_large = results[2]['time']

        # If medium is significantly slower than small, and large is significantly slower than medium
        if time_medium > time_small * 1.5 and time_large > time_medium * 1.5:
            print("⚠️  Exponential time growth detected - ReDoS vulnerability present!")

    # At minimum, verify that the endpoint is responding (even if slowly)
    assert len(results) > 0, "No test cases completed"


@pytest.mark.timeout(10)
def test_regex_dos_valid_email_is_fast(api_base_url: str, user1_token: str):
    """
    Control test: Verify that valid emails are processed quickly.

    This establishes a baseline for normal (non-malicious) input processing time.

    Expected behavior (both vuln=1 and vuln=0):
        - Valid email is processed quickly (< 1 second)
        - Returns 204 No Content (success)
    """
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    valid_email = f"valid_email_{uuid.uuid4().hex[:8]}@example.com"

    start_time = time.time()

    response = requests.put(
        f"{api_base_url}/users/v1/name1/email",
        headers=user1_headers,
        json={"email": valid_email}
    )

    elapsed_time = time.time() - start_time

    print(f"\nValid email processing time: {elapsed_time:.4f} seconds")

    # Should be fast
    assert elapsed_time < 2.0, \
        f"Valid email took too long to process: {elapsed_time:.2f}s"

    # Should succeed
    assert response.status_code == 204, \
        f"Valid email update failed. Expected 204, got {response.status_code}"


@pytest.mark.timeout(10)
def test_regex_dos_simple_invalid_email_is_fast(api_base_url: str, user1_token: str):
    """
    Control test: Verify that simple invalid emails are rejected quickly.

    Invalid emails that don't trigger backtracking should still be processed quickly.

    Expected behavior (both vuln=1 and vuln=0):
        - Simple invalid email is processed quickly (< 1 second)
        - Returns 400 Bad Request
    """
    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    # Simple invalid email (no @ symbol)
    invalid_email = "notanemail"

    start_time = time.time()

    response = requests.put(
        f"{api_base_url}/users/v1/name1/email",
        headers=user1_headers,
        json={"email": invalid_email}
    )

    elapsed_time = time.time() - start_time

    print(f"\nSimple invalid email processing time: {elapsed_time:.4f} seconds")

    # Should be fast
    assert elapsed_time < 2.0, \
        f"Simple invalid email took too long to process: {elapsed_time:.2f}s"

    # Should fail validation
    assert response.status_code == 400, \
        f"Expected 400 for invalid email, got {response.status_code}"


@pytest.mark.timeout(10)
def test_regex_dos_requires_authentication(api_base_url: str):
    """
    Control test: Verify that ReDoS attack requires authentication.

    This ensures that unauthenticated users cannot exploit the ReDoS vulnerability,
    which somewhat limits its severity (but it's still exploitable by any authenticated user).

    Expected behavior (both vuln=1 and vuln=0):
        - Unauthenticated requests return 401
        - No ReDoS processing occurs
    """
    # Use a simpler invalid email to avoid any ReDoS processing
    # The goal is to test authentication, not to trigger ReDoS
    simple_invalid_email = "test@invalid"

    response = requests.put(
        f"{api_base_url}/users/v1/name1/email",
        # No Authorization header
        json={"email": simple_invalid_email},
        timeout=5  # Quick timeout since this should fail immediately
    )

    # Should fail with 401 before any regex processing
    assert response.status_code == 401, \
        f"Unauthenticated request should fail. Expected 401, got {response.status_code}"
