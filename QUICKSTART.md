# VAmPI Quick Start Guide

Get VAmPI running in under 2 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Make (optional, but recommended)

## Step 1: Start VAmPI

```bash
make up
```

Or without Make:
```bash
docker compose up --build -d
```

This will:
- Build all Docker images
- Start the VAmPI API on http://localhost:5000
- Automatically populate the database with 50 users and 5 books per user
- Start a tools container for testing

## Step 2: Wait for Bootstrap

```bash
make logs
```

Look for: `Bootstrap complete! Database is ready for testing.`

## Step 3: Test the API

### Option A: Use Browser
Open http://localhost:5000/ui/ for Swagger UI

### Option B: Use curl
```bash
curl http://localhost:5000/
curl http://localhost:5000/users/v1
```

### Option C: Use Tools Container
```bash
make test

# Inside the container:
http GET http://vampi:5000/users/v1
sqlite3 /vampi/database/database.db "SELECT COUNT(*) FROM users;"
```

## Default Credentials

- **Admin**: `admin` / `pass1`
- **User1**: `name1` / `pass1`
- **User2**: `name2` / `pass2`

Plus 50 generated users with realistic names.

## Common Commands

```bash
make up          # Start services (rebuilds)
make down        # Stop services
make logs        # View logs
make test        # Access tools container
make bootstrap   # Re-populate database
make clean       # Reset everything
make help        # Show all commands
```

## Quick Test Workflow

```bash
# 1. Register a new user
curl -X POST http://localhost:5000/users/v1/register \
  -H "Content-Type: application/json" \
  -d '{"username":"hacker","password":"pass123","email":"hacker@test.com","admin":true}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:5000/users/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"hacker","password":"pass123"}' | jq -r '.auth_token')

# 3. Get books
curl -X GET http://localhost:5000/books/v1 \
  -H "Authorization: Bearer $TOKEN"
```

## Customization

### Different Data Volume
```bash
BOOTSTRAP_USERS=200 BOOTSTRAP_BOOKS_PER_USER=10 make up
```

### Re-bootstrap with Different Data
```bash
BOOTSTRAP_USERS=100 BOOTSTRAP_BOOKS_PER_USER=3 make bootstrap
```

## Troubleshooting

### Check if services are running
```bash
docker compose ps
```

### View logs
```bash
make logs
# or
docker compose logs -f vampi
```

### Reset everything
```bash
make clean
make up
```

## Next Steps

- Read [DOCKER.md](DOCKER.md) for detailed Docker documentation
- Read [CLAUDE.md](CLAUDE.md) for architecture and development guide
- Read [tools/README.md](tools/README.md) for tools documentation
- Explore vulnerabilities at http://localhost:5000/ui/

## Security Warning

⚠️ **VAmPI is intentionally vulnerable!**

- Never expose to the internet
- Only use in isolated test environments
- Do not use in production
- Use for security testing and education only
