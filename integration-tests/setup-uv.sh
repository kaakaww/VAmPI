#!/usr/bin/env bash
#
# Setup integration tests environment with uv
#
# This script creates a virtual environment using uv and installs all dependencies.
# Run this once before running tests with pytest directly.
#
# Usage:
#   cd integration-tests
#   ./setup-uv.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  VAmPI Integration Tests - uv Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗${NC} uv is not installed"
    echo ""
    echo "Install uv with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or visit: https://github.com/astral-sh/uv"
    exit 1
fi

echo -e "${GREEN}✓${NC} uv is installed: $(uv --version)"

# Create virtual environment if it doesn't exist
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠${NC} Virtual environment already exists at .venv"
    read -p "Recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        echo -e "${BLUE}ℹ${NC} Removed existing .venv"
    else
        echo -e "${BLUE}ℹ${NC} Using existing .venv"
    fi
fi

if [ ! -d ".venv" ]; then
    echo -e "${BLUE}ℹ${NC} Creating virtual environment..."
    uv venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created at .venv"
fi

# Activate virtual environment
echo -e "${BLUE}ℹ${NC} Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo -e "${BLUE}ℹ${NC} Installing dependencies..."

# Install dependencies directly (not in editable mode since this is just tests)
uv pip install pytest requests PyJWT pytest-timeout
echo -e "${GREEN}✓${NC} Core dependencies installed"

# Ask if user wants dev dependencies
read -p "Install dev dependencies (pytest-xdist, pytest-cov)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    uv pip install pytest-xdist pytest-cov
    echo -e "${GREEN}✓${NC} Dev dependencies installed"
fi

# Verify installation
echo ""
echo -e "${BLUE}ℹ${NC} Verifying installation..."
pytest --version
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓${NC} Setup complete!"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "To activate the virtual environment:"
echo -e "  ${BLUE}source .venv/bin/activate${NC}"
echo ""
echo "To run tests:"
echo -e "  ${BLUE}pytest -v${NC}"
echo -e "  ${BLUE}pytest test_01_sqli.py -v${NC}"
echo -e "  ${BLUE}pytest -k 'admin' -v${NC}"
echo ""
echo "Or use the convenience script:"
echo -e "  ${BLUE}../run-tests.sh${NC}"
echo ""
