# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VAmPI (Vulnerable API) is an intentionally vulnerable Flask-based REST API designed for security testing, tool evaluation, and educational purposes. The application implements vulnerabilities from the OWASP Top 10 for APIs and includes a global switch to toggle between vulnerable and secure modes.

**IMPORTANT**: This is a deliberately vulnerable application. Do not deploy to production or expose to the internet. All vulnerabilities are intentional and documented.

## Running the Application

### Local Development
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 app.py

# Initialize database (required on first run)
curl http://localhost:5000/createdb
```

The application runs on `http://localhost:5000` by default. Access the Swagger UI at `http://localhost:5000/ui/`.

### Docker (Recommended)

The Docker Compose setup provides a complete testing environment with automatic bootstrapping:

```bash
# Start all services (API + bootstrap + tools) - recommended
make up

# Or using docker compose directly (always use --build)
docker compose up --build -d

# View logs
make logs

# Access tools container for testing
make test
```

This starts:
- **vampi**: Main API on port 5000
- **vampi-bootstrap**: Auto-populates database with sample data (50 users, 5 books each)
- **vampi-tools**: Interactive container with curl, httpie, jq, sqlite3

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

**Quick Docker Commands:**
```bash
# Custom bootstrap size
BOOTSTRAP_USERS=100 BOOTSTRAP_BOOKS_PER_USER=10 make up

# Re-bootstrap database
make bootstrap
# Or with custom settings:
BOOTSTRAP_USERS=200 BOOTSTRAP_BOOKS_PER_USER=10 make bootstrap

# Check database
docker exec vampi-tools sqlite3 /vampi/database/database.db "SELECT COUNT(*) FROM users;"

# Test API from tools container
make test
```

**Available Make Targets:**
- `make up` - Start services (always rebuilds)
- `make down` - Stop services
- `make restart` - Restart services (rebuilds)
- `make logs` - Follow logs
- `make clean` - Remove all containers and volumes
- `make rebuild` - Force rebuild from scratch
- `make bootstrap` - Re-run bootstrap
- `make test` - Access tools container
- `make test-integration` - Run integration tests in Docker
- `make test-integration-verbose` - Run integration tests in Docker (verbose)
- `make test-integration-local` - Run integration tests locally (no docker exec)
- `make help` - Show all commands

### Configuration
Control vulnerability mode and token lifetime via environment variables:
- `vulnerable`: Set to `1` (vulnerable) or `0` (secure). Default: `1`
- `tokentimetolive`: JWT token lifetime in seconds. Default: `60`

Example:
```bash
docker run -e vulnerable=0 -e tokentimetolive=300 -p 5000:5000 erev0s/vampi:latest
```

Or edit `app.py` directly:
- `vuln` variable: controls vulnerability mode
- `alive` variable: controls token lifetime

## Architecture

### Application Structure

The application uses Connexion (a Flask wrapper) with OpenAPI 3.0 specifications to define and validate API endpoints.

**Core Components:**

1. **config.py**: Application initialization and configuration
   - Creates the Connexion app instance (`vuln_app`)
   - Configures SQLAlchemy with SQLite database (`database/database.db`)
   - Sets JWT secret key (intentionally weak: `'random'`)
   - Registers OpenAPI spec from `openapi_specs/openapi3.yml`
   - Custom error handler for ProblemException

2. **app.py**: Entry point
   - Imports configuration from `config.py`
   - Reads environment variables for `vuln` and `alive` settings
   - Starts Flask development server on port 5000

3. **API Views** (`api_views/`):
   - **main.py**: Database initialization and home endpoint
   - **users.py**: User management (register, login, profile, update, delete)
   - **books.py**: Book management (CRUD operations)
   - **json_schemas.py**: JSON schema validators for request validation

4. **Models** (`models/`):
   - **user_model.py**: User model with JWT encoding/decoding, includes SQLi vulnerability
   - **books_model.py**: Book model with user relationship

5. **OpenAPI Specs** (`openapi_specs/`):
   - **openapi3.yml**: Complete API specification that drives endpoint routing via Connexion

6. **Tools** (`tools/`):
   - **bootstrap.py**: Database population utility that creates realistic sample data
   - Generates configurable numbers of users and books for testing
   - See `tools/README.md` for detailed usage

### Key Architectural Patterns

- **Connexion/OpenAPI-driven**: Endpoints are defined in `openapi3.yml` with `operationId` pointing to view functions (e.g., `operationId: api_views.users.register_user`)
- **Conditional Vulnerabilities**: The global `vuln` flag (imported from `app.py`) controls whether vulnerable code paths execute
- **Token-based Auth**: JWT tokens generated on login, validated via `token_validator()` in `api_views/users.py`
- **SQLAlchemy ORM**: Models in `models/` directory with relationships (User has many Books)

### Database Initialization

There are two ways to initialize the database:

1. **Via API Endpoint** (minimal data):
   - `GET /createdb`
   - Creates tables and populates with 3 dummy users and 1 book each:
     - `name1:pass1` (user)
     - `name2:pass2` (user)
     - `admin:pass1` (admin)

2. **Via Bootstrap Tool** (recommended for testing):
   - `python tools/bootstrap.py --users 50 --books-per-user 5`
   - Creates realistic sample data with configurable volume
   - Generates unique usernames, emails, book titles, and secrets
   - Automatically runs in Docker Compose setup

### Authentication Flow

1. User registers via `POST /users/v1/register`
2. User logs in via `POST /users/v1/login` → receives JWT token
3. Token must be included in `Authorization: Bearer <token>` header for protected endpoints
4. `token_validator()` function in `api_views/users.py` validates tokens on protected routes

### Intentional Vulnerabilities

When `vuln=1`, the following vulnerabilities are active:

- **SQLi** (user_model.py:71-78): Raw SQL query in `get_user()`
- **Mass Assignment** (users.py:60-66): Allow `admin` field in registration
- **Broken Object Level Authorization** (books.py:50-60): View any user's book by title
- **Unauthorized Password Change** (users.py:186-192): Change any user's password
- **User/Password Enumeration** (users.py:101-110): Specific error messages reveal valid usernames
- **Regex DoS** (users.py:143-160): Complex regex on email validation
- **Excessive Data Exposure** (users.py:24-26): `/users/v1/_debug` endpoint exposes passwords
- **No Rate Limiting**: All endpoints lack rate limiting
- **Weak JWT Secret**: Secret key is `'random'` (config.py:13)

When `vuln=0`, some (but not all) vulnerabilities are mitigated. The debug endpoint and weak secret remain vulnerable regardless.

## Testing the API

### Manual Testing

Use the Swagger UI at `/ui` or tools like curl/Postman:

```bash
# Initialize database
curl http://localhost:5000/createdb

# Register user
curl -X POST http://localhost:5000/users/v1/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123","email":"test@test.com"}'

# Login
curl -X POST http://localhost:5000/users/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Use token for authenticated requests
curl -X GET http://localhost:5000/books/v1 \
  -H "Authorization: Bearer <token>"
```

### Integration Tests

The `integration-tests/` directory contains comprehensive pytest-based tests that **prove** the vulnerabilities exist. These tests are designed for security education, tool evaluation, and vulnerability validation.

**Running Integration Tests:**

```bash
# Easiest - run locally without docker exec (auto-installs dependencies)
./run-tests.sh
make test-integration-local

# Run in Docker container
make test-integration

# Run with verbose output (shows detailed exploit information)
make test-integration-verbose
./run-tests.sh -vv -s

# Run specific test file
./run-tests.sh test_01_sqli.py
docker exec vampi-tools pytest integration-tests/test_01_sqli.py -v

# Run tests matching keyword
./run-tests.sh -k "admin"
```

**Test Coverage:**

The integration tests cover all 9 major vulnerabilities:

1. **test_01_sqli.py** - SQL Injection vulnerability (API3:2023)
2. **test_02_mass_assignment.py** - Mass assignment privilege escalation (API6:2023)
3. **test_03_bola.py** - Broken Object Level Authorization (API1:2023)
4. **test_04_unauthorized_password_change.py** - Password change authorization bypass (API1:2023)
5. **test_05_user_enumeration.py** - User/password enumeration (API2:2023)
6. **test_06_regex_dos.py** - Regular Expression Denial of Service (API4:2023)
7. **test_07_excessive_data_exposure.py** - Debug endpoint exposing passwords (API3:2023)
8. **test_08_weak_jwt.py** - Weak JWT secret allowing token forgery (API2:2023)
9. **test_09_no_rate_limiting.py** - Lack of rate limiting (API4:2023)

**Important Notes:**

- Tests are **black-box** - they only interact via HTTP API
- Tests use pre-seeded bootstrap data (admin/pass1, name1/pass1, name2/pass2)
- **Passing tests = vulnerabilities are exploitable** (this is by design!)
- Each test includes detailed documentation explaining the vulnerability
- Tests demonstrate real exploits with example payloads
- See `integration-tests/README.md` for comprehensive documentation

**Test Philosophy:**

These tests serve multiple purposes:
- **Education**: Show exactly how vulnerabilities are exploited
- **Validation**: Prove that vulnerabilities exist and are exploitable
- **Tool Testing**: Provide baseline for security scanning tools
- **Regression Testing**: Verify that secure mode (`vuln=0`) patches vulnerabilities

Example test output:
```
======================== test session starts =========================
integration-tests/test_01_sqli.py::test_sqli_basic_or_injection PASSED
integration-tests/test_08_weak_jwt.py::test_weak_jwt_forge_token_for_admin PASSED
======================== 50+ passed in 30.00s ========================
```

**Security Note**: Only run these tests against VAmPI or systems you own. These tests exploit real vulnerabilities and should never be used against production systems or without authorization.

## Dependencies

Key dependencies (see `requirements.txt`):
- **connexion[swagger-ui]==2.14.2**: OpenAPI-driven Flask framework
- **flask==2.2.2**: Web framework
- **flask-sqlalchemy==3.0.3**: ORM
- **PyJWT==2.6.0**: JWT token handling
- **jsonschema==4.17.3**: Request validation

## Important Notes for Development

- Always check the `vuln` flag when modifying security-related code
- OpenAPI spec in `openapi_specs/openapi3.yml` is the source of truth for endpoints
- Database is SQLite stored at `database/database.db` (gitignored)
- All endpoint handlers must be referenced in openapi3.yml via `operationId`
- JWT tokens expire based on `alive` variable (default 60 seconds)
