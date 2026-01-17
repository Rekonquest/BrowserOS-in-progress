"""Tests for build.common.context module."""

from pathlib import Path

import pytest

from build.common.context import ArtifactRegistry, Context


class TestArtifactRegistry:
    """Tests for ArtifactRegistry class."""

    def test_add_and_get_artifact(self):
        """Test adding and retrieving an artifact."""
        registry = ArtifactRegistry()
        test_path = Path("/path/to/artifact")

        registry.add("test_artifact", test_path)
        result = registry.get("test_artifact")

        assert result == test_path

    def test_get_nonexistent_artifact_raises_keyerror(self):
        """Test getting non-existent artifact raises KeyError."""
        registry = ArtifactRegistry()

        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_has_artifact(self):
        """Test checking if artifact exists."""
        registry = ArtifactRegistry()
        test_path = Path("/path/to/artifact")

        assert registry.has("test_artifact") is False

        registry.add("test_artifact", test_path)

        assert registry.has("test_artifact") is True

    def test_overwrite_artifact(self):
        """Test that adding artifact with same name overwrites."""
        registry = ArtifactRegistry()
        path1 = Path("/path/1")
        path2 = Path("/path/2")

        registry.add("artifact", path1)
        assert registry.get("artifact") == path1

        registry.add("artifact", path2)
        assert registry.get("artifact") == path2

    def test_all_artifacts(self):
        """Test getting all artifacts."""
        registry = ArtifactRegistry()
        path1 = Path("/path/1")
        path2 = Path("/path/2")

        registry.add("artifact1", path1)
        registry.add("artifact2", path2)

        all_artifacts = registry.all()

        assert len(all_artifacts) == 2
        assert all_artifacts["artifact1"] == path1
        assert all_artifacts["artifact2"] == path2

    def test_all_returns_copy(self):
        """Test that all() returns a copy, not reference."""
        registry = ArtifactRegistry()
        path1 = Path("/path/1")

        registry.add("artifact1", path1)
        all_artifacts = registry.all()

        # Modify the returned dict
        all_artifacts["new_artifact"] = Path("/path/2")

        # Original registry should be unchanged
        assert registry.has("new_artifact") is False


class TestContextVersionLoading:
    """Tests for Context version loading methods."""

    def test_load_chromium_version(self, temp_dir):
        """Test loading chromium version from file."""
        version_file = temp_dir / "CHROMIUM_VERSION"
        version_content = """MAJOR=137
MINOR=0
BUILD=7151
PATCH=69
"""
        version_file.write_text(version_content)

        version, version_dict = Context._load_chromium_version(temp_dir)

        assert version == "137.0.7151.69"
        assert version_dict["MAJOR"] == "137"
        assert version_dict["MINOR"] == "0"
        assert version_dict["BUILD"] == "7151"
        assert version_dict["PATCH"] == "69"

    def test_load_chromium_version_missing_file(self, temp_dir):
        """Test loading chromium version when file doesn't exist."""
        version, version_dict = Context._load_chromium_version(temp_dir)

        assert version == ""
        assert version_dict == {}

    def test_load_browseros_build_offset(self, temp_dir):
        """Test loading browseros build offset."""
        # Create the expected directory structure
        config_dir = temp_dir / "build" / "config"
        config_dir.mkdir(parents=True)

        offset_file = config_dir / "BROWSEROS_BUILD_OFFSET"
        offset_file.write_text("5")

        offset = Context._load_browseros_build_offset(temp_dir)

        assert offset == "5"

    def test_load_browseros_build_offset_missing_file(self, temp_dir):
        """Test loading browseros build offset when file doesn't exist."""
        offset = Context._load_browseros_build_offset(temp_dir)

        assert offset == ""

    def test_load_semantic_version(self, temp_dir):
        """Test loading semantic version."""
        resources_dir = temp_dir / "resources"
        resources_dir.mkdir(parents=True)

        version_file = resources_dir / "BROWSEROS_VERSION"
        version_content = """BROWSEROS_MAJOR=0
BROWSEROS_MINOR=36
BROWSEROS_BUILD=3
BROWSEROS_PATCH=0
"""
        version_file.write_text(version_content)

        version = Context._load_semantic_version(temp_dir)

        assert version == "0.36.3"

    def test_load_semantic_version_missing_file(self, temp_dir):
        """Test loading semantic version when file doesn't exist."""
        version = Context._load_semantic_version(temp_dir)

        assert version == ""


class TestContextInitialization:
    """Tests for Context initialization."""

    def test_context_calculates_browseros_chromium_version(self, mock_build_root):
        """Test that Context correctly calculates browseros_chromium_version."""
        # Mock build root has CHROMIUM_VERSION with 137.0.7151.69
        # and BROWSEROS_BUILD_OFFSET with 5
        # Expected: 137.0.7156.69 (7151 + 5 = 7156)

        ctx = Context(
            root_dir=mock_build_root, chromium_src=mock_build_root / "chromium_src"
        )

        assert ctx.chromium_version == "137.0.7151.69"
        assert ctx.browseros_build_offset == "5"
        assert ctx.browseros_chromium_version == "137.0.7156.69"

    def test_context_initializes_artifact_registry(self, mock_build_root):
        """Test that Context initializes artifact registry."""
        ctx = Context(
            root_dir=mock_build_root, chromium_src=mock_build_root / "chromium_src"
        )

        assert isinstance(ctx.artifact_registry, ArtifactRegistry)
        assert len(ctx.artifact_registry.all()) == 0

    def test_context_sets_platform_specific_app_names(self, mock_build_root):
        """Test that Context sets platform-specific app names."""
        ctx = Context(
            root_dir=mock_build_root, chromium_src=mock_build_root / "chromium_src"
        )

        # App names should be set based on the current platform
        assert ctx.BROWSEROS_APP_NAME != ""
        assert ctx.CHROMIUM_APP_NAME != ""
        assert ctx.BROWSEROS_APP_BASE_NAME == "BrowserOS"
