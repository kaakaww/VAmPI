#!/usr/bin/env bash
#
# VAmPI Integration Test Runner
#
# This script can be run from anywhere and will automatically:
# - Detect if running inside or outside Docker
# - Clean pytest cache and rebuild test environment
# - Use uv for fast virtual environment management (if available)
# - Reinstall dependencies to ensure fresh environment
# - Set appropriate environment variables
# - Run the integration tests
#
# Usage:
#   ./run-tests.sh              # Run all tests
#   ./run-tests.sh -v           # Verbose output
#   ./run-tests.sh -vv -s       # Very verbose with stdout
#   ./run-tests.sh test_01_sqli.py  # Run specific test file
#   ./run-tests.sh -k "admin"   # Run tests matching keyword

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

# Detect if we're running inside Docker
if [ -f /.dockerenv ]; then
    INSIDE_DOCKER=true
else
    INSIDE_DOCKER=false
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TESTS_DIR="$SCRIPT_DIR/integration-tests"

# Check if integration-tests directory exists
if [ ! -d "$TESTS_DIR" ]; then
    print_error "integration-tests directory not found at $TESTS_DIR"
    exit 1
fi

print_header "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_header "  VAmPI Integration Test Runner"
print_header "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Determine API URL
if [ -n "$VAMPI_BASE_URL" ]; then
    API_URL="$VAMPI_BASE_URL"
elif [ "$INSIDE_DOCKER" = true ]; then
    # Inside Docker, use service name
    API_URL="${VAMPI_HOST:-vampi}:${VAMPI_PORT:-5000}"
    API_URL="http://$API_URL"
else
    # Outside Docker, use localhost
    API_URL="http://localhost:5000"
fi

export VAMPI_BASE_URL="$API_URL"
print_info "API URL: $API_URL"

# Check if API is accessible
print_info "Checking API accessibility..."
if curl -f -s -o /dev/null --max-time 5 "$API_URL/" 2>/dev/null; then
    print_success "API is accessible"
else
    print_error "Cannot reach API at $API_URL"
    echo ""
    echo "Troubleshooting:"
    if [ "$INSIDE_DOCKER" = true ]; then
        echo "  - Ensure VAmPI container is running"
        echo "  - Check: docker ps | grep vampi"
    else
        echo "  - Ensure VAmPI is running: make up"
        echo "  - Check: curl http://localhost:5000/"
        echo "  - If using different port, set: export VAMPI_BASE_URL=http://localhost:PORT"
    fi
    exit 1
fi

# Change to tests directory
cd "$TESTS_DIR"

# Clean up cached files and rebuild
print_info "Cleaning cached files..."
rm -rf __pycache__ .pytest_cache .ruff_cache 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
print_success "Cache cleaned"

# Check for uv (fast Python package manager)
USE_UV=false
if command -v uv &> /dev/null; then
    USE_UV=true
    print_success "uv detected - using fast virtual environment management"
fi

# Setup Python environment
if [ "$USE_UV" = true ]; then
    # Use uv for fast environment management
    print_info "Setting up Python environment with uv..."

    # Check if .venv exists
    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment with uv..."
        uv venv .venv
        print_success "Virtual environment created"
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Install/reinstall dependencies with uv (ensures fresh dependencies)
    print_info "Installing dependencies with uv..."
    uv pip install --reinstall pytest requests PyJWT pytest-timeout --quiet
    print_success "Dependencies installed"

    PYTEST_CMD="pytest"
else
    # Fallback to traditional pip
    print_warning "uv not found, using pip (slower)"

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is not installed"
        exit 1
    fi

    # Check for pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi

    # Install/reinstall dependencies with pip (ensures fresh dependencies)
    print_info "Installing dependencies with pip..."
    if [ -f "requirements.txt" ]; then
        pip3 install -q --upgrade -r requirements.txt || {
            print_error "Failed to install dependencies"
            exit 1
        }
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi

    PYTEST_CMD="python3 -m pytest"
fi

# Build pytest command
PYTEST_ARGS=""
if [ $# -eq 0 ]; then
    # No arguments, run all tests with default verbosity
    PYTEST_ARGS="-v"
else
    # Pass all arguments to pytest
    PYTEST_ARGS="$@"
fi

echo ""
print_info "Running tests..."
if [ "$USE_UV" = true ]; then
    print_info "Environment: uv virtual environment (.venv)"
else
    print_info "Environment: system Python"
fi
echo ""
echo "Command: $PYTEST_CMD $PYTEST_ARGS"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run tests
$PYTEST_CMD $PYTEST_ARGS

# Capture exit code
EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    print_success "All tests passed!"
    echo ""
    echo "Note: Passing tests = vulnerabilities are exploitable (by design)"
else
    print_error "Some tests failed"
    echo ""
    echo "If tests are failing:"
    echo "  - Check that vulnerable=1 in docker-compose.yaml"
    echo "  - Ensure bootstrap completed: make logs"
    echo "  - Try restarting: make restart"
fi

# Deactivate virtual environment if using uv
if [ "$USE_UV" = true ]; then
    deactivate 2>/dev/null || true
fi

exit $EXIT_CODE
