# VAmPI Tools

Utilities for working with the VAmPI vulnerable API.

## bootstrap.py

Populates the database with a configurable amount of sample data for testing.

### Usage

```bash
# Run with defaults (20 users, 5 books per user)
python tools/bootstrap.py

# Customize the number of users and books
python tools/bootstrap.py --users 100 --books-per-user 10

# Create a large dataset
python tools/bootstrap.py --users 500 --books-per-user 3
```

### Arguments

- `--users N` - Number of users to create (default: 20)
- `--books-per-user N` - Number of books per user (default: 5)

### What it Creates

The bootstrap script:
1. Drops and recreates all database tables
2. Creates default users:
   - `admin:pass1` (admin user)
   - `name1:pass1` (regular user)
   - `name2:pass2` (regular user)
3. Generates additional users with:
   - Realistic names (first name + last name)
   - Unique usernames
   - Random passwords
   - Randomly assigned admin status (10% chance)
   - Email addresses
4. Creates books for each user with:
   - Unique titles based on genres and topics
   - Secret content
   - Association to the user

### Docker Usage

When using Docker Compose, the bootstrap runs automatically on startup. Control the amount of data via environment variables:

```bash
# Set in .env file
BOOTSTRAP_USERS=100
BOOTSTRAP_BOOKS_PER_USER=8

# Or pass directly
BOOTSTRAP_USERS=100 docker-compose up -d
```

To manually re-bootstrap from the tools container:

```bash
docker exec -it vampi-tools python tools/bootstrap.py --users 50 --books-per-user 5
```

## Tools Container

The `vampi-tools` container provides a complete environment for testing and interacting with VAmPI:

### Access the Tools Container

```bash
docker exec -it vampi-tools /bin/bash
```

### Available Tools

- **curl** - Make HTTP requests
- **httpie** (http command) - User-friendly HTTP client
- **jq** - JSON processor
- **sqlite3** - Direct database access
- **python** - Run Python scripts
- **All VAmPI tools** - Bootstrap and other utilities

### Example Commands

```bash
# Test the API
curl http://vampi:5000/

# Get all users (pretty output)
http GET http://vampi:5000/users/v1

# Check database stats
sqlite3 /vampi/database/database.db "SELECT COUNT(*) as user_count FROM users;"
sqlite3 /vampi/database/database.db "SELECT COUNT(*) as book_count FROM books;"

# Re-bootstrap with different data
python tools/bootstrap.py --users 200 --books-per-user 7

# Register a new user
http POST http://vampi:5000/users/v1/register \
  username=testuser \
  password=testpass \
  email=test@example.com

# Login
http POST http://vampi:5000/users/v1/login \
  username=testuser \
  password=testpass
```

## Development

To add new tools:

1. Create a new Python script in `tools/`
2. Add appropriate shebang: `#!/usr/bin/env python3`
3. Make it executable: `chmod +x tools/your_tool.py`
4. Update this README with usage instructions
