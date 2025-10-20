# VAmPI StackHawk Scan Configurations

This directory contains StackHawk HawkScan configuration files for testing the VAmPI (Vulnerable API) application. These configurations demonstrate various scanning approaches for API security testing.

## Prerequisites

- VAmPI running locally via Docker Compose: `make up`
- StackHawk API access
- StackHawk Application ID

## Running Scans

Use the StackHawk CLI to run any configuration:

```bash
hawk scan <config-file>
```

## Configuration Files

### 1. stackhawk.yml
**Basic baseline scan**
- Minimal configuration
- Spider-only discovery
- No authentication
- Tests public endpoints only
- **Use case**: Quick smoke test, baseline scanning

### 2. stackhawk-openapi.yml
**OpenAPI-guided scan**
- Uses `openapi_specs/openapi3.yml` spec
- Tests all HTTP methods
- Custom variables for username, book_title, email, password
- No authentication (unauthenticated endpoints only)
- **Use case**: Comprehensive API structure testing without auth
- **Findings**: Discovers SQLi, insecure methods, data exposure issues

### 3. stackhawk-auth-jwt.yml
**JWT authentication scan**
- Logs in as regular user (name1/pass1)
- Extracts JWT token from `/users/v1/login` response
- Uses Bearer token authentication
- Tests authenticated endpoints
- **Use case**: Testing user-level authenticated endpoints

### 4. stackhawk-auth-jwt-openapi.yml
**JWT authentication + OpenAPI-guided scan (RECOMMENDED)**
- Combines JWT auth with OpenAPI spec
- Most comprehensive coverage
- Tests both authenticated and unauthenticated endpoints
- Custom variables for all parameterized endpoints
- **Use case**: Full API security assessment
- **Findings**: Complete vulnerability coverage including BOLA, unauthorized access, SQLi

### 5. stackhawk-auth-jwt-admin.yml
**Admin authentication scan**
- Logs in as admin user (admin/pass1)
- Tests admin-privileged endpoints (DELETE operations)
- OpenAPI-guided
- **Use case**: Testing admin-only functionality and authorization controls

### 6. stackhawk-custom-spider-curl.yml
**Custom spider with curl commands**
- Disables base spider
- Uses curl commands for manual endpoint discovery
- Includes authenticated requests via token extraction
- **Use case**: Custom discovery workflow, testing specific flows

### 7. stackhawk-unauthenticated.yml
**Unauthenticated endpoints focus**
- Explicitly excludes authenticated endpoints
- Only GET and POST methods
- Focuses on public API surface
- **Use case**: Testing public endpoints for info disclosure, enumeration

### 8. stackhawk-sqli-focus.yml
**SQL Injection focused scan**
- SQLi-specific payloads in customVariables
- Targets username parameter vulnerability
- Enables SQLi scanner
- **Use case**: Validating SQLi vulnerabilities (VAmPI has SQLi in `get_user()` when vuln=1)

### 9. stackhawk-debug-endpoint.yml
**Debug endpoint scan**
- Targets `/users/v1/_debug` endpoint specifically
- Tests for excessive data exposure
- Custom spider for targeted discovery
- **Use case**: Testing debug/admin endpoints that expose sensitive data

### 10. stackhawk-mass-assignment.yml
**Mass assignment vulnerability scan**
- Focuses on `/users/v1/register` endpoint
- Tests admin field injection
- **Use case**: Testing for mass assignment vulnerability (setting admin=true during registration)

### 11. stackhawk-auth-multi-user.yml
**Multi-user authentication scan (NEW MULTI-AUTH FEATURE)**
- Scans with multiple user profiles (USER and ADMIN)
- Tests authorization boundaries and privilege escalation
- OpenAPI-guided with comprehensive coverage
- **Profiles**:
  - USER: Regular user (name1/pass1)
  - ADMIN: Privileged user (admin/pass1) with `isPrivileged: true`
- **Use case**: Identifying Broken Object Level Authorization (BOLA), Broken Function Level Authorization (BFLA), and privilege escalation vulnerabilities
- **Key benefit**: Detects when regular users can access admin-only functions or other users' data

This configuration uses the new multi-auth capability to test with different privilege levels in a single scan, helping identify authorization issues like:
- Regular users accessing admin endpoints (BFLA)
- Users accessing other users' resources (BOLA)
- Privilege escalation vulnerabilities

## VAmPI Vulnerabilities Detected

When VAmPI runs with `vuln=1` (default), StackHawk detects:

1. **SQL Injection** (High) - user_model.py:71-78
   - Detected in: stackhawk-openapi.yml, stackhawk-sqli-focus.yml
   - Payload: `admin' OR 1=1--`

2. **Mass Assignment** (Medium) - users.py:60-66
   - Detected in: stackhawk-mass-assignment.yml
   - Payload: `{"username":"test","password":"pass","email":"test@test.com","admin":true}`

3. **Broken Object Level Authorization** (High)
   - Detected in: stackhawk-auth-jwt-openapi.yml
   - Access other users' books

4. **Excessive Data Exposure** (High)
   - Detected in: stackhawk-debug-endpoint.yml
   - `/users/v1/_debug` exposes passwords

5. **Weak JWT Secret** (High)
   - Secret is `'random'` (config.py:13)
   - Allows token forgery

## Integration with VAmPI

All scans target the local VAmPI instance at `http://localhost:5000`. Ensure VAmPI is running:

```bash
# Start VAmPI with bootstrap data
make up

# Verify it's running
curl http://localhost:5000/
```

Bootstrap creates test users:
- `admin` / `pass1` (admin)
- `name1` / `pass1` (user)
- `name2` / `pass2` (user)

## Best Practices

1. **Start with OpenAPI**: Use `stackhawk-openapi.yml` for initial discovery
2. **Add Authentication**: Progress to `stackhawk-auth-jwt-openapi.yml` for full coverage
3. **Test Authorization (RECOMMENDED)**: Use `stackhawk-auth-multi-user.yml` to test with multiple privilege levels and identify BOLA/BFLA vulnerabilities
4. **Test Admin Paths**: Use `stackhawk-auth-jwt-admin.yml` for privileged operations
5. **Targeted Testing**: Use focused configs (sqli, mass-assignment, debug) for specific vulnerabilities

## Platform Links

Each scan creates a unique scan ID with direct links in the output.
