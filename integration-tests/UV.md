# Using uv with VAmPI Integration Tests

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip and provides better dependency resolution.

## Why uv?

- ⚡ **Blazingly fast** - 10-100x faster than pip
- 🔒 **Better resolution** - More reliable dependency resolution
- 🎯 **Modern** - Built for modern Python development
- 🐍 **Compatible** - Drop-in replacement for pip in virtual environments

## Installation

### macOS/Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Using pip

```bash
pip install uv
```

### Using Homebrew (macOS)

```bash
brew install uv
```

For more installation options, see [uv documentation](https://github.com/astral-sh/uv#installation).

## Usage with VAmPI Tests

### Option 1: Automatic (Recommended)

The `run-tests.sh` script automatically detects and uses uv if available:

```bash
# From project root
./run-tests.sh

# uv will be automatically used if installed
# Output will show: "✓ uv detected - using fast virtual environment management"
```

### Option 2: Manual Setup

If you want more control, manually set up the environment:

```bash
# Navigate to integration-tests
cd integration-tests

# Run setup script
./setup-uv.sh

# Activate the virtual environment
source .venv/bin/activate

# Run tests directly
pytest -v
pytest test_08_weak_jwt.py -v
pytest -k "admin" -v
```

### Option 3: Command-by-Command

```bash
cd integration-tests

# Create virtual environment
uv venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv pip install -e .

# Or from requirements.txt
uv pip install -r requirements.txt

# Run tests
pytest -v
```

## Project Structure

The integration tests use a modern Python project structure:

```
integration-tests/
├── pyproject.toml       # Modern Python project config (preferred by uv)
├── requirements.txt     # Traditional requirements (fallback)
├── setup-uv.sh         # Convenient setup script
├── .venv/              # Virtual environment (created by uv)
└── test_*.py           # Test files
```

## pyproject.toml

The tests use `pyproject.toml` for dependency management, which is preferred by modern tools like uv:

```toml
[project]
name = "vampi-integration-tests"
dependencies = [
    "pytest>=7.4.0",
    "requests>=2.31.0",
    "PyJWT>=2.6.0",
    "pytest-timeout>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest-xdist>=3.3.0",  # For parallel test execution
    "pytest-cov>=4.1.0",    # For coverage reporting
]
```

## Advanced Usage

### Install with Dev Dependencies

```bash
uv pip install -e ".[dev]"
```

### Parallel Test Execution

With dev dependencies installed:

```bash
pytest -n auto  # Auto-detect CPU count
pytest -n 4     # Use 4 parallel workers
```

### Update Dependencies

```bash
# Update all dependencies
uv pip install --upgrade -e .

# Or update specific package
uv pip install --upgrade pytest
```

### Generate Requirements File from pyproject.toml

```bash
uv pip compile pyproject.toml -o requirements.txt
```

## Performance Comparison

Example installation times on a typical machine:

| Tool | First Install | Cached Install |
|------|--------------|----------------|
| pip | ~15 seconds | ~8 seconds |
| **uv** | **~1 second** | **~0.3 seconds** |

*Results vary based on system and number of dependencies*

## Troubleshooting

### Virtual Environment Not Activating

```bash
# Ensure you're in the integration-tests directory
cd integration-tests

# Source the activation script
source .venv/bin/activate

# Verify activation
which python  # Should show .venv/bin/python
```

### Dependency Issues

```bash
# Clear and recreate environment
rm -rf .venv
./setup-uv.sh
```

### uv Not Found After Installation

```bash
# Add uv to your PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

## Comparison with Traditional Setup

### Traditional (pip)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Slow
pytest -v
```

### Modern (uv)

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .  # Fast!
pytest -v
```

Or just:

```bash
./run-tests.sh  # Automatically uses uv if available
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Set up uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Create virtual environment
  run: uv venv

- name: Install dependencies
  run: |
    source .venv/bin/activate
    uv pip install -e integration-tests/

- name: Run tests
  run: |
    source .venv/bin/activate
    pytest integration-tests/ -v
```

## Additional Resources

- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [uv Documentation](https://github.com/astral-sh/uv#readme)
- [Python Packaging Guide](https://packaging.python.org/)
- [pyproject.toml Specification](https://peps.python.org/pep-0621/)

## FAQ

**Q: Do I need to use uv?**
A: No! The tests work with regular pip. uv is optional but recommended for speed.

**Q: Can I switch between pip and uv?**
A: Yes, they're compatible. Just use different virtual environments.

**Q: What if uv isn't available?**
A: The `run-tests.sh` script automatically falls back to pip.

**Q: Does this work on Windows?**
A: Yes, but activate command is `.venv\Scripts\activate` on Windows.
