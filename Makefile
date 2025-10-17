.PHONY: help up down restart logs clean build rebuild bootstrap test test-integration test-integration-verbose test-integration-local

help:
	@echo "VAmPI Development Commands"
	@echo "=========================="
	@echo ""
	@echo "  make up                      - Start all services (rebuilds images)"
	@echo "  make down                    - Stop all services"
	@echo "  make restart                 - Restart all services (rebuilds images)"
	@echo "  make logs                    - Follow logs from all services"
	@echo "  make clean                   - Stop and remove all containers and volumes"
	@echo "  make build                   - Build all Docker images"
	@echo "  make rebuild                 - Force rebuild all images from scratch"
	@echo "  make bootstrap               - Re-run bootstrap with default settings"
	@echo "  make test                    - Access tools container for testing"
	@echo "  make test-integration        - Run integration tests in Docker"
	@echo "  make test-integration-verbose - Run integration tests in Docker (verbose)"
	@echo "  make test-integration-local  - Run integration tests locally (auto-installs deps)"
	@echo ""
	@echo "Environment Variables:"
	@echo "  BOOTSTRAP_USERS=N              - Number of users to create (default: 50)"
	@echo "  BOOTSTRAP_BOOKS_PER_USER=N     - Books per user (default: 5)"
	@echo ""
	@echo "Examples:"
	@echo "  make up"
	@echo "  BOOTSTRAP_USERS=100 make up"
	@echo "  make bootstrap"
	@echo "  make test"

up:
	docker compose up --build -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f

clean:
	docker compose down -v
	@echo "All containers and volumes removed"

build:
	docker compose build

rebuild:
	docker compose build --no-cache

bootstrap:
	docker exec vampi-tools python tools/bootstrap.py --users ${BOOTSTRAP_USERS:-50} --books-per-user ${BOOTSTRAP_BOOKS_PER_USER:-5}

test:
	docker exec -it vampi-tools /bin/bash

test-integration:
	@echo "Running VAmPI integration tests..."
	@echo "These tests PROVE vulnerabilities exist (passing tests = exploitable vulnerabilities)"
	@echo ""
	docker exec vampi-tools sh -c "cd /vampi && pip install -q -r integration-tests/requirements.txt && pytest integration-tests/ -v --tb=short"

test-integration-verbose:
	@echo "Running VAmPI integration tests with verbose output..."
	@echo "These tests PROVE vulnerabilities exist (passing tests = exploitable vulnerabilities)"
	@echo ""
	docker exec vampi-tools sh -c "cd /vampi && pip install -q -r integration-tests/requirements.txt && pytest integration-tests/ -vv -s"

test-integration-local:
	@echo "Running VAmPI integration tests locally..."
	@echo "These tests PROVE vulnerabilities exist (passing tests = exploitable vulnerabilities)"
	@echo ""
	./run-tests.sh
