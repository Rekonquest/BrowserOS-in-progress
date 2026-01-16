# BrowserOS Test Suite

This directory contains the test suite for the BrowserOS build system.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=build --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_context.py
```

### Run specific test class or function
```bash
pytest tests/test_context.py::TestArtifactRegistry
pytest tests/test_context.py::TestArtifactRegistry::test_add_and_get_artifact
```

### Run tests with specific markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Organization

- `conftest.py` - Shared fixtures and pytest configuration
- `test_*.py` - Test modules organized by source module
- Tests are organized into classes by feature/component

## Test Fixtures

### Available Fixtures

- `temp_dir` - Temporary directory for test files
- `mock_chromium_version_file` - Mock CHROMIUM_VERSION file
- `mock_build_root` - Complete mock build root directory structure
- `mock_env_vars` - Mock environment variables (auto-cleanup)

## Writing Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test functions: `test_<what_it_tests>`

### Example Test

```python
import pytest
from build.common.utils import normalize_path

class TestPathUtilities:
    """Tests for path utilities."""

    def test_normalize_path_with_string(self):
        """Test normalizing a string path."""
        result = normalize_path("/usr/local/bin")
        assert isinstance(result, Path)
```

## Coverage Goals

- Minimum coverage: 80%
- Critical modules (context, utils, config): 90%+
- All new code should include tests

## Test Markers

- `@pytest.mark.unit` - Unit tests (isolated, fast)
- `@pytest.mark.integration` - Integration tests (may require external resources)
- `@pytest.mark.slow` - Slow tests (can be skipped for quick checks)
