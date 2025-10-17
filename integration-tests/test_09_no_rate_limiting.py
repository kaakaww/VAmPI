"""
Test Lack of Rate Limiting Vulnerability (API4:2023 Unrestricted Resource Consumption)

This test demonstrates the absence of rate limiting on all API endpoints.
Without rate limiting, attackers can:
1. Perform brute-force attacks on authentication
2. Enumerate users and resources
3. Launch denial-of-service attacks
4. Scrape all data from the API

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

Vulnerability Location: All endpoints (no rate limiting implemented anywhere)
"""

import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def test_no_rate_limiting_on_login(api_base_url: str, default_credentials: dict):
    """
    Test that login endpoint has no rate limiting.

    This enables brute-force attacks on user passwords. An attacker can try
    thousands of passwords without being blocked.

    Expected behavior (vuln=1):
        - Can make unlimited login attempts
        - No rate limiting or account lockout
        - Perfect for brute-force attacks

    Expected behavior (vuln=0):
        - Rate limiting blocks excessive attempts
        - Returns 429 (Too Many Requests)
        - May implement account lockout
    """
    admin_username = default_credentials["admin"]["username"]
    wrong_password = "wrongpassword"

    # Attempt multiple failed logins in rapid succession
    num_attempts = 20
    successful_attempts = 0
    start_time = time.time()

    print(f"\n🔓 Attempting {num_attempts} rapid login attempts...")

    for i in range(num_attempts):
        response = requests.post(
            f"{api_base_url}/users/v1/login",
            json={"username": admin_username, "password": f"{wrong_password}{i}"}
        )

        # All attempts should go through (200 status, even if auth fails)
        if response.status_code == 200:
            successful_attempts += 1
        elif response.status_code == 429:  # Rate limited
            print(f"Rate limiting detected at attempt {i + 1}")
            break

    elapsed = time.time() - start_time

    print(f"Completed {successful_attempts}/{num_attempts} requests in {elapsed:.2f}s")
    print(f"Average: {elapsed/num_attempts:.3f}s per request")

    # When vulnerable, all attempts should succeed (no rate limiting)
    assert successful_attempts == num_attempts, \
        f"Rate limiting appears to be implemented. Only {successful_attempts}/{num_attempts} " \
        f"requests succeeded."

    print("⚠️  No rate limiting detected - brute-force attacks are possible!")


def test_no_rate_limiting_on_registration(api_base_url: str):
    """
    Test that registration endpoint has no rate limiting.

    This enables:
    - Spam account creation
    - Resource exhaustion (filling database)
    - Automated bot registrations

    Expected behavior (vuln=1):
        - Can create unlimited accounts rapidly
        - No CAPTCHA or rate limiting

    Expected behavior (vuln=0):
        - Rate limiting blocks excessive registrations
        - CAPTCHA or other anti-automation measures
    """
    num_attempts = 15
    successful_registrations = 0
    start_time = time.time()

    print(f"\n🔓 Attempting {num_attempts} rapid registrations...")

    for i in range(num_attempts):
        username = f"spam_user_{int(time.time() * 1000)}_{i}"
        response = requests.post(
            f"{api_base_url}/users/v1/register",
            json={
                "username": username,
                "password": "spampass",
                "email": f"{username}@spam.com"
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                successful_registrations += 1
        elif response.status_code == 429:
            print(f"Rate limiting detected at registration {i + 1}")
            break

    elapsed = time.time() - start_time

    print(f"Created {successful_registrations}/{num_attempts} accounts in {elapsed:.2f}s")

    # When vulnerable, most/all registrations should succeed
    assert successful_registrations >= num_attempts * 0.9, \
        f"Rate limiting may be implemented. Only {successful_registrations}/{num_attempts} succeeded."

    print("⚠️  No rate limiting on registration - spam account creation possible!")


def test_no_rate_limiting_on_api_endpoints(api_base_url: str, user1_token: str):
    """
    Test that protected API endpoints have no rate limiting.

    This enables:
    - Data scraping at high speed
    - API abuse
    - Denial of service through resource exhaustion

    Expected behavior (vuln=1):
        - Can make unlimited requests
        - No throttling

    Expected behavior (vuln=0):
        - Rate limiting protects resources
        - Returns 429 after threshold
    """
    headers = {"Authorization": f"Bearer {user1_token}"}
    num_requests = 50
    successful_requests = 0
    start_time = time.time()

    print(f"\n🔓 Attempting {num_requests} rapid API requests...")

    for i in range(num_requests):
        response = requests.get(
            f"{api_base_url}/users/v1",
            headers=headers
        )

        if response.status_code == 200:
            successful_requests += 1
        elif response.status_code == 429:
            print(f"Rate limiting detected at request {i + 1}")
            break

    elapsed = time.time() - start_time

    print(f"Completed {successful_requests}/{num_requests} requests in {elapsed:.2f}s")
    print(f"Requests per second: {successful_requests/elapsed:.1f}")

    # When vulnerable, all requests should succeed
    assert successful_requests == num_requests, \
        f"Rate limiting may be implemented. Only {successful_requests}/{num_requests} succeeded."

    print("⚠️  No rate limiting on API endpoints - data scraping at full speed possible!")


def test_no_rate_limiting_concurrent_requests(api_base_url: str, user1_token: str):
    """
    Test that concurrent requests are not rate limited.

    This tests whether the API can handle many simultaneous connections,
    which could be used for:
    - Distributed brute-force attacks
    - DDoS attacks
    - Resource exhaustion

    Expected behavior (vuln=1):
        - Accepts unlimited concurrent connections
        - No connection limits

    Expected behavior (vuln=0):
        - Connection limits or rate limiting
        - Graceful degradation under load
    """
    headers = {"Authorization": f"Bearer {user1_token}"}
    num_concurrent = 10  # Number of concurrent requests
    num_requests = 5     # Requests per thread

    print(f"\n🔓 Attempting {num_concurrent * num_requests} concurrent requests...")

    def make_requests(thread_id):
        """Make multiple requests from a single thread"""
        results = []
        for i in range(num_requests):
            try:
                response = requests.get(
                    f"{api_base_url}/users/v1",
                    headers=headers,
                    timeout=10
                )
                results.append({
                    "thread": thread_id,
                    "request": i,
                    "status": response.status_code,
                    "success": response.status_code == 200
                })
            except requests.exceptions.Timeout:
                results.append({
                    "thread": thread_id,
                    "request": i,
                    "status": "TIMEOUT",
                    "success": False
                })
        return results

    start_time = time.time()
    all_results = []

    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [executor.submit(make_requests, i) for i in range(num_concurrent)]

        for future in as_completed(futures):
            all_results.extend(future.result())

    elapsed = time.time() - start_time

    successful = sum(1 for r in all_results if r["success"])
    total = len(all_results)

    print(f"Completed {successful}/{total} concurrent requests in {elapsed:.2f}s")
    print(f"Overall rate: {successful/elapsed:.1f} requests/second")

    # When vulnerable, most requests should succeed
    success_rate = successful / total
    assert success_rate > 0.8, \
        f"Many concurrent requests failed ({success_rate:.0%} success rate). " \
        f"May have connection limits or rate limiting."

    print("⚠️  No rate limiting on concurrent requests!")


def test_no_rate_limiting_password_brute_force_simulation(api_base_url: str, default_credentials: dict):
    """
    Simulate a realistic password brute-force attack.

    This demonstrates how an attacker would use the lack of rate limiting
    to try common passwords against a known username.

    Expected behavior (vuln=1):
        - Can try hundreds of passwords
        - No account lockout
        - Perfect for brute-force

    Expected behavior (vuln=0):
        - Rate limiting blocks attack
        - Account lockout after N failed attempts
        - CAPTCHA required
    """
    target_username = default_credentials["admin"]["username"]

    # Common passwords to try (in real attack, this would be millions)
    common_passwords = [
        "password", "123456", "admin", "letmein", "welcome",
        "monkey", "dragon", "master", "sunshine", "princess",
        "qwerty", "password123", "admin123", "root", "toor",
        "test", "guest", "user", "default", "changeme"
    ]

    print(f"\n🔓 Simulating brute-force attack on user '{target_username}'...")
    print(f"Trying {len(common_passwords)} common passwords...")

    start_time = time.time()
    attempts = 0
    rate_limited = False

    for password in common_passwords:
        response = requests.post(
            f"{api_base_url}/users/v1/login",
            json={"username": target_username, "password": password}
        )

        attempts += 1

        if response.status_code == 429:
            rate_limited = True
            print(f"✓ Rate limiting triggered after {attempts} attempts")
            break
        elif response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ Found password: {password}")
                break

    elapsed = time.time() - start_time

    if not rate_limited:
        print(f"⚠️  Completed {attempts} password attempts in {elapsed:.2f}s without rate limiting!")
        print(f"   Attack rate: {attempts/elapsed:.1f} attempts/second")
        print(f"   A real attacker could try millions of passwords!")

    # When vulnerable, should be able to try all passwords
    assert not rate_limited, \
        f"Rate limiting detected after {attempts} attempts - vulnerability mitigated"


def test_no_rate_limiting_user_enumeration_attack(api_base_url: str):
    """
    Demonstrate user enumeration at scale enabled by lack of rate limiting.

    An attacker can quickly enumerate thousands of usernames by:
    1. Trying common usernames
    2. Using leaked email lists
    3. Generating sequential usernames

    Expected behavior (vuln=1):
        - Can enumerate users at high speed
        - No rate limiting

    Expected behavior (vuln=0):
        - Rate limiting slows enumeration
        - Makes large-scale enumeration impractical
    """
    # Common username patterns to try
    username_patterns = [
        "admin", "administrator", "root", "user", "test",
        "demo", "guest", "operator", "support", "webmaster",
        "name1", "name2", "name3", "alice", "bob",
        "charlie", "david", "emma", "frank", "george"
    ]

    print(f"\n🔓 Attempting to enumerate {len(username_patterns)} usernames...")

    start_time = time.time()
    found_users = []
    attempts = 0

    for username in username_patterns:
        response = requests.post(
            f"{api_base_url}/users/v1/login",
            json={"username": username, "password": "dummypassword"}
        )

        attempts += 1

        if response.status_code == 429:
            print(f"Rate limiting detected at attempt {attempts}")
            break

        if response.status_code == 200:
            data = response.json()
            message = data.get("message", "").lower()

            # Check for user enumeration indicators
            if "password" in message and "correct" in message:
                found_users.append(username)

    elapsed = time.time() - start_time

    print(f"Enumeration complete:")
    print(f"  - Tested {attempts} usernames in {elapsed:.2f}s")
    print(f"  - Found {len(found_users)} valid users: {found_users}")
    print(f"  - Enumeration rate: {attempts/elapsed:.1f} attempts/second")

    # When vulnerable, should complete all attempts
    assert attempts >= len(username_patterns) * 0.9, \
        "Rate limiting prevented full enumeration"

    print("⚠️  No rate limiting - large-scale user enumeration is possible!")


def test_no_rate_limiting_best_practices():
    """
    Document rate limiting best practices that are violated.

    This test serves as documentation for proper rate limiting implementation.

    Rate Limiting Best Practices:
    1. Implement rate limiting on all public endpoints
    2. Use tiered rate limits (per IP, per user, per API key)
    3. Implement exponential backoff for repeated failures
    4. Add CAPTCHA for sensitive operations (login, registration)
    5. Implement account lockout after N failed login attempts
    6. Return 429 (Too Many Requests) with Retry-After header
    7. Monitor and alert on rate limit violations

    Current violations in VAmPI:
    - ✗ No rate limiting on any endpoint
    - ✗ No CAPTCHA protection
    - ✗ No account lockout
    - ✗ No IP-based throttling
    - ✗ No user-based throttling
    """
    print("\n⚠️  Rate Limiting Violations Detected:")
    print("   1. No rate limiting on any endpoint")
    print("   2. No CAPTCHA for authentication")
    print("   3. No account lockout mechanism")
    print("   4. No IP-based throttling")
    print("   5. No user-based throttling")
    print("\n   Recommendations:")
    print("   1. Implement Flask-Limiter or similar library")
    print("   2. Set appropriate limits per endpoint:")
    print("      - Login: 5 attempts per 15 minutes per IP")
    print("      - Registration: 3 attempts per hour per IP")
    print("      - API endpoints: 100 requests per minute per user")
    print("   3. Add CAPTCHA for sensitive operations")
    print("   4. Implement account lockout (temporary or permanent)")
    print("   5. Monitor rate limit violations for security incidents")
    print("   6. Return proper 429 responses with Retry-After headers")

    # This test always passes - it's for documentation
    assert True
