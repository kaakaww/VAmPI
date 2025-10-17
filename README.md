# VAmPI
**The Vulnerable API** *(Based on OpenAPI 3)*
![vampi](https://i.imgur.com/zR0quKf.jpg)

[![Docker Image CI](https://github.com/erev0s/VAmPI/actions/workflows/docker-image.yml/badge.svg)](https://github.com/erev0s/VAmPI/actions/workflows/docker-image.yml) ![Docker Pulls](https://img.shields.io/docker/pulls/erev0s/vampi)


VAmPI is a vulnerable API made with Flask and it includes vulnerabilities from the OWASP top 10 vulnerabilities for APIs. It was created as I wanted a vulnerable API to evaluate the efficiency of tools used to detect security issues in APIs. It includes a switch on/off to allow the API to be vulnerable or not while testing. This allows to cover better the cases for false positives/negatives. VAmPI can also be used for learning/teaching purposes. You can find a bit more details about the vulnerabilities in [erev0s.com](https://erev0s.com/blog/vampi-vulnerable-api-security-testing/).


#### Features
 - Based on OWASP Top 10 vulnerabilities for APIs.
 - OpenAPI3 specs and Postman Collection included.
 - Global switch on/off to have a vulnerable environment or not.
 - Token-Based Authentication (Adjust lifetime from within app.py)
 - Available Swagger UI to directly interact with the API

VAmPI's flow of actions is going like this: an unregistered user can see minimal information about the dummy users included in the API. A user can register and then login to be allowed using the token received during login to post a book. For a book posted the data accepted are the title and a secret about that book. Each book is unique for every user and only the owner of the book should be allowed to view the secret.

A quick rundown of the actions included can be seen in the following table:

| **Action** |            **Path**           |                     **Details**                    |
|:----------:|:-----------------------------:|:--------------------------------------------------:|
|     GET    |           /createdb           | Creates and populates the database with dummy data |
|     GET    |               /               |                     VAmPI home                     |
|     GET    |               /me             |           Displays the user that is logged in       |
|     GET    |           /users/v1           |      Displays all users with basic information     |
|     GET    |        /users/v1/_debug       |         Displays all details for all users         |
|    POST    |       /users/v1/register      |                  Register new user                 |
|    POST    |        /users/v1/login        |                   Login to VAmPI                   |
|     GET    |      /users/v1/{username}     |              Displays user by username             |
|   DELETE   |      /users/v1/{username}     |       Deletes user by username (Only Admins)       |
|     PUT    |   /users/v1/{username}/email  |             Update a single users email            |
|     PUT    | /users/v1/{username}/password |                Update users password               |
|     GET    |           /books/v1           |                 Retrieves all books                |
|    POST    |           /books/v1           |                    Add new book                    |
|     GET    |        /books/v1/{book}       |      Retrieves book by title along with secret     |

For more details you can either run VAmPI and visit `http://127.0.0.1:5000/ui/` or use a service like the [swagger editor](https://editor.swagger.io) supplying the OpenAPI specification which can be found in the directory `openapi_specs`.


#### List of Vulnerabilities
 - SQLi Injection
 - Unauthorized Password Change
 - Broken Object Level Authorization
 - Mass Assignment
 - Excessive Data Exposure through debug endpoint
 - User and Password Enumeration
 - RegexDOS (Denial of Service)
 - Lack of Resources & Rate Limiting
 - JWT authentication bypass via weak signing key



 ## Run it
It is a Flask application so in order to run it you can install all requirements and then run the `app.py`.
To install all requirements simply run `pip3 install -r requirements.txt` and then `python3 app.py`.

Or if you prefer you can also run it through docker or docker compose.

 #### Run it through Docker

 - Available in [Dockerhub](https://hub.docker.com/r/erev0s/vampi)
~~~~
docker run -p 5000:5000 erev0s/vampi:latest
~~~~

[Note: if you run Docker on newer versions of the MacOS, use `-p 5001:5000` to avoid conflicting with the AirPlay Receiver service. Alternatively, you could disable the AirPlay Receiver service in your System Preferences -> Sharing settings.]

  #### Run it through Docker Compose
`docker-compose` contains two instances, one instance with the secure configuration on port 5001 and another with insecure on port 5002:
~~~~
docker-compose up -d
~~~~

## Available Swagger UI :rocket:
Visit the path `/ui` where you are running the API and a Swagger UI will be available to help you get started!
~~~~
http://127.0.0.1:5000/ui/
~~~~

## Customizing token timeout and vulnerable environment or not
If you would like to alter the timeout of the token created after login or if you want to change the environment **not** to be vulnerable then you can use a few ways depending how you run the application.

 - If you run it like normal with `python3 app.py` then all you have to do is edit the `alive` and `vuln` variables defined in the `app.py` itself. The `alive` variable is measured in seconds, so if you put `100`, then the token expires after 100 seconds. The `vuln` variable is like boolean, if you set it to `1` then the application is vulnerable, and if you set it to `0` the application is not vulnerable.
 - If you run it through Docker, then you must either pass environment variables to the `docker run` command or edit the `Dockerfile` and rebuild. 
   - Docker run example: `docker run -d -e vulnerable=0 -e tokentimetolive=300 -p 5000:5000 erev0s/vampi:latest`
     - One nice feature to running it this way is you can startup a 2nd container with `vulnerable=1` on a different port and flip easily between the two.

   - In the Dockerfile you will find two environment variables being set, the `ENV vulnerable=1` and the `ENV tokentimetolive=60`. Feel free to change it before running the docker build command.


## Integration Tests

VAmPI includes comprehensive integration tests that **prove** each vulnerability is exploitable. These tests serve as:
- 🎓 **Educational examples** of how vulnerabilities are exploited
- 🔍 **Validation tools** to verify vulnerabilities exist
- 🛠️ **Benchmarks** for security scanning tools
- 📊 **Regression tests** to verify fixes work (when `vulnerable=0`)

### Quick Start

```bash
# Start VAmPI
make up

# Run tests locally (easiest - no docker exec)
./run-tests.sh

# Or run in Docker
make test-integration

# Run specific test
./run-tests.sh test_08_weak_jwt.py -v
```

**Note**: Passing tests = vulnerabilities are exploitable (by design!)

See [`integration-tests/README.md`](integration-tests/README.md) for complete documentation.

## StackHawk Customizations

This fork includes significant enhancements for security testing, tool evaluation, and developer experience:

### 🧪 Comprehensive Integration Test Suite

**60 black-box integration tests** that prove vulnerabilities are exploitable:

- **Test Coverage**: 9 OWASP API Security Top 10 vulnerabilities
- **Language**: Python + pytest for readability and ease of use
- **Approach**: Black-box testing via HTTP API (no privileged access)
- **Purpose**: Educational examples, vulnerability validation, security tool benchmarking

Tests include detailed documentation explaining what each vulnerability is, why it's dangerous, how to exploit it, and how to fix it.

**Test Files**:
- `test_00_health.py` - Pre-flight checks (API accessibility, bootstrap data, vulnerable mode)
- `test_01_sqli.py` - SQL Injection (5 tests)
- `test_02_mass_assignment.py` - Mass assignment privilege escalation (4 tests)
- `test_03_bola.py` - Broken Object Level Authorization (6 tests)
- `test_04_unauthorized_password_change.py` - Password change authorization bypass (6 tests)
- `test_05_user_enumeration.py` - User/password enumeration (6 tests)
- `test_06_regex_dos.py` - Regular Expression Denial of Service (5 tests)
- `test_07_excessive_data_exposure.py` - Debug endpoint exposing passwords (7 tests)
- `test_08_weak_jwt.py` - Weak JWT secret allowing token forgery (7 tests)
- `test_09_no_rate_limiting.py` - Lack of rate limiting (7 tests)

### 🐳 Modernized Docker Compose Stack

**Three-service architecture** for automated testing and development:

1. **vampi** - Main vulnerable API service
   - Exposed on `localhost:5000`
   - Configurable via environment variables
   - Health checks for reliable startup

2. **vampi-bootstrap** - Automatic database population
   - Runs once on startup to seed database
   - Creates 50 users with 5 books each (configurable)
   - Generates realistic sample data for testing
   - Set `BOOTSTRAP_USERS` and `BOOTSTRAP_BOOKS_PER_USER` to customize

3. **vampi-tools** - Interactive testing container
   - Pre-installed tools: curl, httpie, jq, sqlite3, pytest
   - Access via `make test` or `docker exec -it vampi-tools sh`
   - Shared volume for database inspection
   - Ideal for manual testing and exploration

### 🛠️ Developer Tools & Infrastructure

**Makefile** with convenient commands:
```bash
make up              # Start all services (always rebuilds)
make down            # Stop services
make restart         # Restart and rebuild
make logs            # Follow logs
make bootstrap       # Re-run database bootstrap
make test            # Access tools container
make test-integration # Run tests in Docker
```

**run-tests.sh** - Standalone test runner:
- Works inside and outside Docker (no `docker exec` needed)
- Auto-detects and uses `uv` if available (10-100x faster than pip)
- Cleans cache and reinstalls dependencies for fresh test runs
- Checks API accessibility before running tests
- Passes all arguments to pytest

**tools/bootstrap.py** - Database population utility:
- Creates configurable number of users and books
- Generates realistic usernames, emails, titles, and secrets
- 10% of users are admins by default
- Can be run manually or via Docker service

### 📚 Enhanced Documentation

- **CLAUDE.md** - Comprehensive guide for Claude Code and developers
- **DOCKER.md** - Complete Docker Compose documentation
- **QUICKSTART.md** - Integration tests quick start guide
- **integration-tests/README.md** - Detailed test documentation with examples
- **integration-tests/UV.md** - uv package manager setup and usage

### ⚡ Performance Optimizations

- **uv support**: Fast Python package manager (10-100x faster dependency installation)
- **Virtual environments**: Isolated test environments with `pyproject.toml`
- **Cache management**: Automatic cleanup of pytest cache and bytecode
- **Parallel execution**: Tests can run with pytest-xdist for speed

### 🎯 Key Features

✅ **Zero-config testing** - `./run-tests.sh` handles everything automatically
✅ **Dynamic test data** - Tests query API for data, work with any bootstrap size
✅ **Isolated environments** - Tests create temporary users to avoid interference
✅ **Clear output** - Tests print exploit details and vulnerability explanations
✅ **Fast iteration** - uv installs 12 packages in ~15ms vs 8-15 seconds with pip
✅ **CI/CD ready** - Tests work in GitHub Actions, GitLab CI, etc.

### 📖 Quick Command Reference

```bash
# Start everything
make up

# Run all tests
./run-tests.sh

# Run specific test with verbose output
./run-tests.sh test_08_weak_jwt.py -vv -s

# Run tests matching keyword
./run-tests.sh -k "admin"

# Customize bootstrap data
BOOTSTRAP_USERS=100 BOOTSTRAP_BOOKS_PER_USER=10 make up

# Access tools container for manual testing
make test
```

### 🔍 Example Test Output

```
✓ JWT token generation and validation working
⚠️ CRITICAL: Debug endpoint exposes passwords!
🔓 Forged JWT token for admin user
⚠️ WARNING: Response took 3.45s - potential ReDoS vulnerability!
======================== 60 passed in 1.75s ========================
```

For detailed documentation, see:
- [Integration Tests README](integration-tests/README.md)
- [Docker Compose Guide](DOCKER.md)
- [Quick Start Guide](QUICKSTART.md)

## Frequently asked questions
 - **There is a database error upon reaching endpoints!**
   - Make sure to issue a request towards the endpoint `/createdb` in order to populate the database, or use `make up` which automatically bootstraps the database.

 [Picture from freepik - www.freepik.com](https://www.freepik.com/vectors/party)

