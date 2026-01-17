"""Test fixtures for BuildContext and related components."""

from pathlib import Path
from typing import Any

import pytest

from build.common.artifacts import ArtifactManager
from build.common.build_config import BuildConfig
from build.common.paths import PathManager
from build.common.version import VersionManager


@pytest.fixture
def temp_build_dir(tmp_path: Path) -> Path:
    """
    Create a temporary build directory with standard structure.

    Creates:
    - chromium_src/
    - chromium_src/out/Default/
    - build/
    - logs/
    - CHROMIUM_VERSION
    - BROWSEROS_VERSION
    - BROWSEROS_BUILD_OFFSET

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path to root build directory
    """
    # Create directory structure
    root = tmp_path / "build_root"
    root.mkdir()

    chromium_src = root / "chromium_src"
    chromium_src.mkdir()

    out_dir = chromium_src / "out" / "Default"
    out_dir.mkdir(parents=True)

    build_dir = root / "build"
    build_dir.mkdir()

    logs_dir = root / "logs"
    logs_dir.mkdir()

    # Create version files
    chromium_version = root / "CHROMIUM_VERSION"
    chromium_version.write_text("137.0.7151.69\n")

    browseros_version = root / "BROWSEROS_VERSION"
    browseros_version.write_text("0.36.3\n")

    browseros_build_offset = root / "BROWSEROS_BUILD_OFFSET"
    browseros_build_offset.write_text("5\n")

    return root


@pytest.fixture
def mock_chromium_src(tmp_path: Path) -> Path:
    """
    Create a mock Chromium source directory.

    Creates:
    - chromium_src/
    - chromium_src/out/Default/
    - chromium_src/chrome/
    - chromium_src/chrome/app/
    - chromium_src/BUILD.gn

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path to chromium_src
    """
    chromium_src = tmp_path / "chromium_src"
    chromium_src.mkdir()

    # Create standard Chromium directory structure
    (chromium_src / "out" / "Default").mkdir(parents=True)
    (chromium_src / "chrome" / "app").mkdir(parents=True)
    (chromium_src / "BUILD.gn").write_text("# Mock BUILD.gn\n")

    return chromium_src


@pytest.fixture
def mock_version_manager(temp_build_dir: Path) -> VersionManager:
    """
    Create a VersionManager with test data.

    Args:
        temp_build_dir: Temporary build directory with version files

    Returns:
        Configured VersionManager
    """
    return VersionManager(root_dir=temp_build_dir)


@pytest.fixture
def mock_path_manager(temp_build_dir: Path, mock_chromium_src: Path) -> PathManager:
    """
    Create a PathManager with test paths.

    Args:
        temp_build_dir: Temporary build directory
        mock_chromium_src: Mock Chromium source directory

    Returns:
        Configured PathManager
    """
    return PathManager(
        root_dir=temp_build_dir,
        chromium_src=mock_chromium_src,
        out_dir="out/Default",
        architecture="x64",
    )


@pytest.fixture
def mock_artifact_manager() -> ArtifactManager:
    """
    Create an empty ArtifactManager for testing.

    Returns:
        Empty ArtifactManager
    """
    return ArtifactManager()


@pytest.fixture
def mock_build_config() -> BuildConfig:
    """
    Create a BuildConfig with test settings.

    Returns:
        Test BuildConfig
    """
    return BuildConfig(
        platform="macos",
        architecture="arm64",
        build_type="debug",
        app_base_name="BrowserOS",
    )


@pytest.fixture
def mock_context(
    temp_build_dir: Path,
    mock_chromium_src: Path,
    mock_version_manager: VersionManager,
    mock_path_manager: PathManager,
    mock_artifact_manager: ArtifactManager,
    mock_build_config: BuildConfig,
) -> dict[str, Any]:
    """
    Create a mock build context with all components.

    This fixture provides a dictionary mimicking the BuildContext
    with all necessary components for testing modules.

    Args:
        temp_build_dir: Temporary build directory
        mock_chromium_src: Mock Chromium source
        mock_version_manager: Version manager
        mock_path_manager: Path manager
        mock_artifact_manager: Artifact manager
        mock_build_config: Build configuration

    Returns:
        Dictionary with context components

    Example:
        def test_module(mock_context):
            module = MyModule()
            module.execute(mock_context)
            assert mock_context["artifacts"].has("my_artifact")
    """
    return {
        "root_dir": temp_build_dir,
        "chromium_src": mock_chromium_src,
        "versions": mock_version_manager,
        "paths": mock_path_manager,
        "artifacts": mock_artifact_manager,
        "config": mock_build_config,
        "platform": mock_build_config.platform,
        "architecture": mock_build_config.architecture,
        "build_type": mock_build_config.build_type,
    }


__all__ = [
    "temp_build_dir",
    "mock_chromium_src",
    "mock_version_manager",
    "mock_path_manager",
    "mock_artifact_manager",
    "mock_build_config",
    "mock_context",
]
