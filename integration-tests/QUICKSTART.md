# Integration Tests Quick Start

## Prerequisites

1. **VAmPI API must be running**:
   ```bash
   # From project root
   make up
   ```

2. **Wait for bootstrap to complete** (check logs):
   ```bash
   make logs
   # Wait for "Bootstrap complete!" message
   ```

## Running Tests

### Using run-tests.sh (Recommended - No Docker exec)

```bash
# From project root - automatically handles everything
./run-tests.sh

# Or using Make
make test-integration-local

# With verbose output
./run-tests.sh -v

# Very verbose with stdout
./run-tests.sh -vv -s

# Run specific test file
./run-tests.sh test_01_sqli.py

# Run specific test function
./run-tests.sh test_08_weak_jwt.py::test_weak_jwt_forge_token_for_admin -v

# Run tests matching pattern
./run-tests.sh -k "enumeration"

# Stop on first failure
./run-tests.sh -x
```

The `run-tests.sh` script automatically:
- Detects if running inside or outside Docker
- **Uses uv if available** (10-100x faster than pip!)
- Checks API accessibility
- Installs dependencies if needed
- Sets correct API URL
- Provides helpful error messages

💡 **Tip**: Install [uv](https://github.com/astral-sh/uv) for blazing-fast dependency installation:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Using Make with Docker

```bash
# From project root
make test-integration

# Run with verbose output (shows exploit details)
make test-integration-verbose
```

### Using Docker Directly

```bash
# From project root
docker exec vampi-tools pytest integration-tests/ -v
```

### Manual Local Setup

**With uv (fast):**
```bash
cd integration-tests

# One-time setup (creates .venv and installs deps)
./setup-uv.sh

# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest -v
```

**Traditional (pip):**
```bash
cd integration-tests

# Install dependencies (first time only)
pip install -r requirements.txt

# Set API URL (if not localhost)
export VAMPI_BASE_URL=http://localhost:5000

# Run all tests
pytest -v
```

📚 See [UV.md](UV.md) for detailed uv documentation.

## Test Order

Tests run in alphabetical order by filename:

1. `test_00_health.py` - Health checks (API accessibility, bootstrap data)
2. `test_01_sqli.py` - SQL Injection
3. `test_02_mass_assignment.py` - Mass assignment
4. `test_03_bola.py` - BOLA
5. `test_04_unauthorized_password_change.py` - Password change
6. `test_05_user_enumeration.py` - User enumeration
7. `test_06_regex_dos.py` - ReDoS
8. `test_07_excessive_data_exposure.py` - Data exposure
9. `test_08_weak_jwt.py` - Weak JWT
10. `test_09_no_rate_limiting.py` - Rate limiting

## Expected Results

**All tests should PASS when VAmPI is running in vulnerable mode (`vulnerable=1`).**

- ✅ **Passing test** = Vulnerability is exploitable (by design!)
- ❌ **Failing test** = Either vulnerability is patched, API is down, or test needs fixing

Example output:
```
======================== test session starts =========================
integration-tests/test_00_health.py::test_api_is_accessible PASSED
integration-tests/test_01_sqli.py::test_sqli_basic_or_injection PASSED
integration-tests/test_08_weak_jwt.py::test_weak_jwt_forge_token_for_admin PASSED
======================== 59 passed in 45.23s =========================
```

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
docker exec vampi-tools sqlite3 /vampi/database/database.db "SELECT COUNT(*) FROM users;"
# Should show 50+ users
```

### Token Expiration Errors

Tokens expire after 300 seconds (5 minutes) by default. If tests take longer, tokens may expire. The test fixtures automatically get fresh tokens for each test.

### Tests Running Slowly

Some tests (especially ReDoS and rate limiting) may be slow by design. Use the `-v` flag to see which test is running.

## Test Configuration

Configure tests via environment variables:

```bash
# API URL
export VAMPI_BASE_URL=http://vampi:5000

# Run tests
pytest -v
```

## Selective Test Execution

```bash
# Run only fast tests (skip ReDoS)
pytest -v -m "not slow"

# Run only SQL injection tests
pytest test_01_sqli.py -v

# Run tests matching a keyword
pytest -k "admin" -v

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

## Test Output

- **Normal mode**: Shows test names and pass/fail status
- **Verbose mode (`-v`)**: Shows detailed test information
- **Very verbose (`-vv`)**: Shows assertion details
- **With stdout (`-s`)**: Shows print statements from tests

## Getting Help

```bash
# Show all pytest options
pytest --help

# Show available markers
pytest --markers

# Show available fixtures
pytest --fixtures
```

## CI/CD Integration

See `README.md` for GitHub Actions example and CI/CD integration patterns.
