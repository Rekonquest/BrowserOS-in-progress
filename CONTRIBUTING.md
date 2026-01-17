# Contributing to NexusOS

Thank you for your interest in contributing to NexusOS! This is an independent open-source project focused on building a privacy-first Chromium browser with native AI agent capabilities.

## 🏗️ Repository Structure

NexusOS is organized into main components:
- **Browser Build System** - Python-based Chromium build system (packages/browseros/)
- **Agent Submodule** - Chrome extension with AI features (packages/browseros-agent/)
- **Chromium Patches** - Custom patches applied to base Chromium (packages/browseros/chromium_patches/)

## 🚀 Getting Started

### Prerequisites
- Git with submodule support
- Python 3.12 or higher
- Platform-specific build tools (see below)

### Quick Setup

```bash
# Clone repository with submodules
git clone --recursive https://github.com/Rekonquest/BrowserOS-in-progress.git
cd BrowserOS-in-progress

# Initialize submodules (if not cloned with --recursive)
git submodule update --init --recursive

# Set up Python environment
cd packages/browseros
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install -e ".[dev]"
```

## 🔧 Development Workflow

### 1. Browser Build System Development

The build system is written in modern Python 3.12+ with full type hints and comprehensive testing.

**Key directories:**
```
packages/browseros/
├── build/              # Build modules and CLI
│   ├── cli/           # CLI commands
│   ├── common/        # Shared utilities
│   └── modules/       # Build pipeline modules
├── chromium_patches/  # Patches applied to Chromium
├── resources/         # Browser resources
└── tests/             # Test suite
```

**Running tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=build --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

**Code quality:**
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
pyright

# Security audit
pip-audit
```

### 2. Agent Development

The agent is a Chrome extension located in the `packages/browseros-agent/` submodule.

**Setup:**
```bash
cd packages/browseros-agent

# See packages/browseros-agent/CONTRIBUTING.md for details
# (if the submodule includes its own contributing guide)
```

### 3. Chromium Patches

Patches are located in `packages/browseros/chromium_patches/` and organized by feature.

**Adding a new patch:**
1. Create your patch file in the appropriate directory
2. Update the patch series file if needed
3. Test the patch applies cleanly
4. Document the purpose in commit message

## 📝 Contribution Guidelines

### Code Style

**Python:**
- Follow PEP 8 and PEP 257
- Use type hints for all functions
- Line length: 88 characters (Black style)
- Use f-strings for formatting
- Docstrings: Google style

**C++/Chromium:**
- Follow Chromium coding style
- Keep patches minimal and focused
- Document why patches are needed

### Commit Messages

Use conventional commits format:

```
type(scope): brief description

Longer description if needed

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `docs`: Documentation changes
- `chore`: Maintenance tasks
- `security`: Security fixes

**Examples:**
```
feat(agent): add new automation tool
fix(build): resolve macOS compilation error
refactor(common): modernize config loading
security: update cryptography to fix CVE-2024-26130
```

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch from `main`
   ```bash
   git checkout -b feature/my-awesome-feature
   ```
3. **Make** your changes
   - Write tests for new functionality
   - Update documentation
   - Follow code style guidelines
4. **Test** your changes
   ```bash
   pytest
   ruff check .
   pyright
   ```
5. **Commit** your changes with clear messages
6. **Push** to your fork
   ```bash
   git push origin feature/my-awesome-feature
   ```
7. **Open** a Pull Request
   - Describe what changed and why
   - Reference any related issues
   - Ensure CI passes

### What We Look For

✅ **Good PRs have:**
- Clear purpose and scope
- Tests for new functionality
- Updated documentation
- Clean commit history
- Passing CI checks

❌ **Avoid:**
- Mixing unrelated changes
- Breaking existing functionality
- Skipping tests
- Large, unfocused PRs

## 🧪 Testing

### Test Structure

```
packages/browseros/tests/
├── conftest.py              # Pytest configuration
├── fixtures/                # Shared test fixtures
├── integration/             # Integration tests
├── test_*.py               # Unit tests
└── README.md               # Test documentation
```

### Writing Tests

```python
import pytest
from build.common import Config

def test_config_loading():
    """Test configuration loads correctly."""
    config = Config.from_file("test_config.yaml")
    assert config.chromium_version is not None

@pytest.mark.integration
def test_build_pipeline():
    """Test full build pipeline integration."""
    # Test implementation
    pass
```

### Running Specific Tests

```bash
# Run single test file
pytest tests/test_config.py

# Run single test function
pytest tests/test_config.py::test_config_loading

# Run with verbose output
pytest -v

# Run with debugging
pytest --pdb
```

## 🔒 Security

### Reporting Vulnerabilities

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. See [SECURITY.md](.github/SECURITY.md) for reporting instructions
3. Wait for acknowledgment before disclosing

### Security Best Practices

- Never commit secrets or API keys
- Use `.env` files for local configuration (already gitignored)
- Audit dependencies with `pip-audit`
- Follow secure coding practices

## 📚 Resources

### Documentation
- [Build System Modernization](packages/browseros/BUILD_SYSTEM_MODERNIZATION.md)
- [Migration Guide](packages/browseros/MIGRATION_GUIDE.md)
- [Test Documentation](packages/browseros/tests/README.md)
- [Windows Build Notes](WINDOWS_BUILD_ASSESSMENT.md)

### External Resources
- [Chromium Development](https://www.chromium.org/developers/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)

## 💡 Development Tips

### Building Chromium

```bash
# Full build
browseros build

# Development build (faster)
browseros build --dev

# Clean build
browseros build --clean
```

### Debugging

```python
# Use rich for better debugging output
from rich import print
print(my_object)  # Beautiful formatting

# Logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug information")
```

### Performance

- Use pytest markers to skip slow tests during development
- Leverage pytest fixtures for test isolation
- Use pytest-cov to identify untested code

## ❓ Questions?

- Check existing [issues](https://github.com/Rekonquest/BrowserOS-in-progress/issues)
- Open a new issue for bugs or feature requests
- Read the documentation in the repository

## 📜 License

By contributing to NexusOS, you agree that your contributions will be licensed under the AGPL-3.0 license.

---

Thank you for contributing to NexusOS! Every contribution, no matter how small, makes a difference.
