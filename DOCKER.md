# VAmPI Docker Setup Guide

Complete Docker setup for running VAmPI with automatic bootstrapping and testing tools.

## Quick Start

```bash
# Using Makefile (recommended - always rebuilds)
make up

# Or using docker compose directly (with --build flag)
docker compose up --build -d

# View logs
docker compose logs -f
# Or: make logs

# Check service status
docker compose ps
```

**Note:** Always use `--build` flag or `make up` to ensure containers are rebuilt with latest code changes.

The setup will:
1. Start the VAmPI API on `http://localhost:5000`
2. Automatically bootstrap the database with 50 users and 5 books per user
3. Start a tools container for testing and interaction

## Services

### 1. vampi (Main API Service)

The vulnerable API server.

- **Port**: 5000
- **URL**: http://localhost:5000
- **Swagger UI**: http://localhost:5000/ui
- **Container**: vampi-vulnerable

**Environment Variables**:
- `vulnerable=1` - Enable vulnerable mode (default)
- `tokentimetolive=300` - JWT token lifetime in seconds

### 2. vampi-bootstrap (Init Service)

Automatically runs on startup to populate the database with sample data. Exits when complete.

- **Container**: vampi-bootstrap
- **Run once**: Yes (restart: no)

**Environment Variables**:
- `BOOTSTRAP_USERS=50` - Number of users to create
- `BOOTSTRAP_BOOKS_PER_USER=5` - Books per user

### 3. vampi-tools (Testing Container)

Interactive container with tools for testing and database access.

- **Container**: vampi-tools
- **Purpose**: Interactive testing environment

**Access**:
```bash
docker exec -it vampi-tools /bin/bash
```

## Configuration

### Using Environment Variables

Create a `.env` file (see `.env.example`):

```bash
BOOTSTRAP_USERS=100
BOOTSTRAP_BOOKS_PER_USER=8
```

Then start the services:
```bash
docker-compose up -d
```

### Inline Environment Variables

```bash
BOOTSTRAP_USERS=200 docker-compose up -d
```

## Makefile Commands

A Makefile is provided for common operations:

```bash
make help          # Show all available commands
make up            # Start services (rebuilds images)
make down          # Stop all services
make restart       # Restart services (rebuilds images)
make logs          # Follow logs
make clean         # Remove all containers and volumes
make build         # Build all images
make rebuild       # Force rebuild from scratch (no cache)
make bootstrap     # Re-run bootstrap
make test          # Access tools container
```

**Examples:**
```bash
# Start with custom bootstrap settings
BOOTSTRAP_USERS=100 make up

# Re-bootstrap with different data
BOOTSTRAP_USERS=200 BOOTSTRAP_BOOKS_PER_USER=10 make bootstrap

# Access tools container
make test
```

## Common Operations

### View API Logs

```bash
docker-compose logs -f vampi
```

### View Bootstrap Progress

```bash
docker-compose logs vampi-bootstrap
```

### Access Tools Container

```bash
docker exec -it vampi-tools /bin/bash

# Inside the container
curl http://vampi:5000/
http GET http://vampi:5000/users/v1
sqlite3 /vampi/database/database.db "SELECT COUNT(*) FROM users;"
```

### Re-bootstrap Database

```bash
# From host
docker exec vampi-tools python tools/bootstrap.py --users 100 --books-per-user 10

# Or restart the bootstrap service
docker-compose restart vampi-bootstrap
```

### Rebuild Containers

```bash
# Rebuild all (using Makefile)
make rebuild

# Or using docker compose
docker compose build --no-cache

# Rebuild specific service
docker compose build --no-cache vampi
docker compose build --no-cache vampi-tools

# Rebuild and restart
make restart
```

### Reset Everything

```bash
# Using Makefile
make clean
make up

# Or using docker compose
docker compose down -v
docker compose up --build -d
```

## Testing Workflow

### 1. Start Services

```bash
docker-compose up -d
```

### 2. Wait for Bootstrap

```bash
# Watch bootstrap complete
docker-compose logs -f vampi-bootstrap

# You should see:
# "Bootstrap complete! Database is ready for testing."
```

### 3. Test API

```bash
# From host
curl http://localhost:5000/
curl http://localhost:5000/users/v1

# Or use tools container
docker exec -it vampi-tools /bin/bash
http GET http://vampi:5000/users/v1
```

### 4. Inspect Database

```bash
docker exec -it vampi-tools sqlite3 /vampi/database/database.db

sqlite> SELECT COUNT(*) FROM users;
sqlite> SELECT username, email, admin FROM users LIMIT 10;
sqlite> SELECT COUNT(*) FROM books;
sqlite> .quit
```

### 5. Test Vulnerabilities

```bash
# From tools container
docker exec -it vampi-tools /bin/bash

# Register a user
http POST http://vampi:5000/users/v1/register \
  username=attacker \
  password=pass123 \
  email=attacker@example.com \
  admin=true

# Login
TOKEN=$(http POST http://vampi:5000/users/v1/login \
  username=attacker \
  password=pass123 | jq -r '.auth_token')

# Use token
http GET http://vampi:5000/books/v1 "Authorization: Bearer $TOKEN"
```

## Customization

### Different Bootstrap Sizes

For light testing (fast):
```bash
BOOTSTRAP_USERS=10 BOOTSTRAP_BOOKS_PER_USER=3 docker-compose up -d
```

For stress testing (large dataset):
```bash
BOOTSTRAP_USERS=500 BOOTSTRAP_BOOKS_PER_USER=10 docker-compose up -d
```

### Skip Bootstrap

To skip automatic bootstrapping, comment out or remove the `vampi-bootstrap` service from docker-compose.yaml.

Then manually bootstrap:
```bash
docker exec vampi-tools python tools/bootstrap.py --users 20 --books-per-user 5
```

### Custom Token Lifetime

Edit `docker-compose.yaml`:
```yaml
services:
  vampi:
    environment:
      - tokentimetolive=600  # 10 minutes
```

## Troubleshooting

### Bootstrap fails

```bash
# Check logs
docker-compose logs vampi-bootstrap

# Manually run bootstrap
docker exec -it vampi-tools python tools/bootstrap.py --users 20 --books-per-user 5
```

### API not responding

```bash
# Check health
docker-compose ps

# Check logs
docker-compose logs vampi

# Restart service
docker-compose restart vampi
```

### Database issues

```bash
# Reset database by recreating volumes
docker-compose down -v
docker-compose up -d
```

### Cannot connect to tools container

```bash
# Check if running
docker-compose ps

# Start if stopped
docker-compose up -d vampi-tools

# Get shell
docker exec -it vampi-tools /bin/bash
```

## Network Architecture

All services run on the `vampi-network` bridge network:

- **vampi**: Main API (accessible from host on port 5000)
- **vampi-bootstrap**: Init container (internal only)
- **vampi-tools**: Tools container (internal only, shell access via docker exec)

Services communicate using container names:
- `http://vampi:5000` (from inside containers)
- `http://localhost:5000` (from host)

## Volume Management

### vampi-data Volume

Shared persistent volume for the SQLite database.

```bash
# List volumes
docker volume ls | grep vampi

# Inspect volume
docker volume inspect vampi_vampi-data

# Backup database
docker cp vampi-vulnerable:/vampi/database/database.db ./backup.db

# Restore database
docker cp ./backup.db vampi-vulnerable:/vampi/database/database.db
```

## Production Notes

**WARNING**: This is a deliberately vulnerable application. Never expose to the internet or use in production!

For demonstration/training purposes:
- Run on isolated networks only
- Use behind authentication/VPN
- Monitor and log all access
- Reset data regularly
