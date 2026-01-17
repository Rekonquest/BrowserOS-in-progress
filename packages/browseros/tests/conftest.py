"""Pytest configuration and shared fixtures for BrowserOS tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Import all fixtures from fixtures package
pytest_plugins = [
    "tests.fixtures.context",
    "tests.fixtures.modules",
]


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_chromium_version_file(temp_dir: Path) -> Path:
    """Create a mock CHROMIUM_VERSION file for testing."""
    version_file = temp_dir / "CHROMIUM_VERSION"
    version_content = """MAJOR=137
MINOR=0
BUILD=7151
PATCH=69
"""
    version_file.write_text(version_content)
    return version_file


@pytest.fixture
def mock_build_root(temp_dir: Path, mock_chromium_version_file: Path) -> Path:
    """Create a mock build root directory structure."""
    # Create necessary subdirectories
    (temp_dir / "build").mkdir()
    (temp_dir / "build" / "config").mkdir()
    (temp_dir / "resources").mkdir()
    (temp_dir / "chromium_src").mkdir()
    (temp_dir / "out").mkdir()

    # Create BROWSEROS_VERSION file in resources/ with KEY=VALUE format
    version_file = temp_dir / "resources" / "BROWSEROS_VERSION"
    version_content = """BROWSEROS_MAJOR=0
BROWSEROS_MINOR=36
BROWSEROS_BUILD=3
BROWSEROS_PATCH=0
"""
    version_file.write_text(version_content)

    # Create BROWSEROS_BUILD_OFFSET file in build/config/
    offset_file = temp_dir / "build" / "config" / "BROWSEROS_BUILD_OFFSET"
    offset_file.write_text("5")

    return temp_dir


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Provide and cleanup mock environment variables."""
    original_env = os.environ.copy()

    # Set up mock environment
    test_env = {
        "BROWSEROS_ROOT": "/tmp/test_browseros",
        "CHROMIUM_SRC": "/tmp/test_browseros/chromium_src",
    }
    os.environ.update(test_env)

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
