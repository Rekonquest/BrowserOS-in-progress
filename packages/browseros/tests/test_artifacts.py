"""Tests for build.common.artifacts module."""

from pathlib import Path

import pytest

from build.common.artifacts import ArtifactManager, ArtifactMetadata


class TestArtifactManager:
    """Tests for ArtifactManager class."""

    def test_add_single_artifact(self):
        """Test adding a single artifact."""
        artifacts = ArtifactManager()
        test_path = Path("/path/to/artifact")

        artifacts.add("test_artifact", test_path)

        assert artifacts.has("test_artifact")
        assert artifacts.get("test_artifact") == test_path

    def test_add_artifact_with_metadata(self):
        """Test adding artifact with metadata."""
        artifacts = ArtifactManager()
        test_path = Path("/path/to/signed.app")

        artifacts.add(
            "signed_app",
            test_path,
            size=1024,
            checksum="abc123",
            signature="sig456",
            metadata={"key": "value"},
        )

        meta = artifacts.get_metadata("signed_app")
        assert meta.size == 1024
        assert meta.checksum == "abc123"
        assert meta.signature == "sig456"
        assert meta.metadata["key"] == "value"

    def test_add_multiple_paths_to_same_artifact(self):
        """Test adding multiple paths to same artifact name."""
        artifacts = ArtifactManager()
        path1 = Path("/path/1")
        path2 = Path("/path/2")

        artifacts.add("artifact", path1)
        artifacts.add("artifact", path2)

        # Should have both paths
        all_paths = artifacts.get_all("artifact")
        assert len(all_paths) == 2
        assert path1 in all_paths
        assert path2 in all_paths

        # Primary path should be first
        assert artifacts.get("artifact") == path1

    def test_add_multiple(self):
        """Test adding multiple paths at once."""
        artifacts = ArtifactManager()
        paths = [Path("/path/1"), Path("/path/2"), Path("/path/3")]

        artifacts.add_multiple("multi_artifact", paths)

        all_paths = artifacts.get_all("multi_artifact")
        assert len(all_paths) == 3
        assert all_paths == paths

    def test_get_nonexistent_artifact_raises_error(self):
        """Test getting non-existent artifact raises KeyError."""
        artifacts = ArtifactManager()

        with pytest.raises(KeyError, match="Artifact not found"):
            artifacts.get("nonexistent")

    def test_get_all_nonexistent_artifact_raises_error(self):
        """Test getting all paths for non-existent artifact raises KeyError."""
        artifacts = ArtifactManager()

        with pytest.raises(KeyError, match="Artifact not found"):
            artifacts.get_all("nonexistent")

    def test_has_artifact(self):
        """Test checking if artifact exists."""
        artifacts = ArtifactManager()
        test_path = Path("/path/to/artifact")

        assert artifacts.has("test_artifact") is False

        artifacts.add("test_artifact", test_path)

        assert artifacts.has("test_artifact") is True

    def test_remove_artifact(self):
        """Test removing an artifact."""
        artifacts = ArtifactManager()
        artifacts.add("artifact", Path("/path"))

        assert artifacts.has("artifact")

        artifacts.remove("artifact")

        assert not artifacts.has("artifact")

    def test_remove_nonexistent_raises_error(self):
        """Test removing non-existent artifact raises KeyError."""
        artifacts = ArtifactManager()

        with pytest.raises(KeyError, match="Artifact not found"):
            artifacts.remove("nonexistent")

    def test_list_artifacts(self):
        """Test listing all artifact names."""
        artifacts = ArtifactManager()
        artifacts.add("artifact1", Path("/path/1"))
        artifacts.add("artifact2", Path("/path/2"))
        artifacts.add("artifact3", Path("/path/3"))

        artifact_list = artifacts.list_artifacts()

        assert len(artifact_list) == 3
        assert "artifact1" in artifact_list
        assert "artifact2" in artifact_list
        assert "artifact3" in artifact_list

    def test_all_metadata(self):
        """Test getting all metadata."""
        artifacts = ArtifactManager()
        artifacts.add("artifact1", Path("/path/1"), size=100)
        artifacts.add("artifact2", Path("/path/2"), size=200)

        all_meta = artifacts.all_metadata()

        assert len(all_meta) == 2
        assert all_meta["artifact1"].size == 100
        assert all_meta["artifact2"].size == 200

    def test_clear(self):
        """Test clearing all artifacts."""
        artifacts = ArtifactManager()
        artifacts.add("artifact1", Path("/path/1"))
        artifacts.add("artifact2", Path("/path/2"))

        assert len(artifacts) == 2

        artifacts.clear()

        assert len(artifacts) == 0
        assert not artifacts.has("artifact1")
        assert not artifacts.has("artifact2")

    def test_len(self):
        """Test getting number of artifacts."""
        artifacts = ArtifactManager()

        assert len(artifacts) == 0

        artifacts.add("artifact1", Path("/path/1"))
        assert len(artifacts) == 1

        artifacts.add("artifact2", Path("/path/2"))
        assert len(artifacts) == 2

    def test_contains_operator(self):
        """Test 'in' operator support."""
        artifacts = ArtifactManager()
        artifacts.add("artifact", Path("/path"))

        assert "artifact" in artifacts
        assert "nonexistent" not in artifacts

    def test_repr(self):
        """Test string representation."""
        artifacts = ArtifactManager()
        artifacts.add("artifact1", Path("/path/1"))
        artifacts.add("artifact2", Path("/path/2"))

        repr_str = repr(artifacts)

        assert "ArtifactManager" in repr_str
        assert "2" in repr_str


class TestArtifactMetadata:
    """Tests for ArtifactMetadata class."""

    def test_create_metadata(self):
        """Test creating artifact metadata."""
        meta = ArtifactMetadata(
            name="test",
            paths=[Path("/path/1"), Path("/path/2")],
            size=1024,
            checksum="abc123",
        )

        assert meta.name == "test"
        assert len(meta.paths) == 2
        assert meta.size == 1024
        assert meta.checksum == "abc123"

    def test_add_path(self):
        """Test adding path to metadata."""
        meta = ArtifactMetadata(name="test", paths=[Path("/path/1")])

        assert len(meta.paths) == 1

        meta.add_path(Path("/path/2"))

        assert len(meta.paths) == 2

    def test_add_duplicate_path(self):
        """Test that duplicate paths are not added."""
        meta = ArtifactMetadata(name="test", paths=[Path("/path/1")])

        meta.add_path(Path("/path/1"))  # Duplicate

        # Should still be 1
        assert len(meta.paths) == 1

    def test_primary_path(self):
        """Test getting primary path."""
        paths = [Path("/path/1"), Path("/path/2")]
        meta = ArtifactMetadata(name="test", paths=paths)

        # Primary is first path
        assert meta.primary_path == paths[0]

    def test_primary_path_empty(self):
        """Test primary path when no paths."""
        meta = ArtifactMetadata(name="test")

        assert meta.primary_path is None

    def test_path_count(self):
        """Test getting path count."""
        meta = ArtifactMetadata(name="test")
        assert meta.path_count == 0

        meta.add_path(Path("/path/1"))
        assert meta.path_count == 1

        meta.add_path(Path("/path/2"))
        assert meta.path_count == 2


class TestArtifactManagerIntegration:
    """Integration tests for ArtifactManager."""

    def test_typical_build_workflow(self):
        """Test typical artifact workflow during build."""
        artifacts = ArtifactManager()

        # Step 1: Compile creates built app
        artifacts.add("built_app", Path("/out/BrowserOS.app"))
        assert artifacts.has("built_app")

        # Step 2: Sign creates signed app
        built_app = artifacts.get("built_app")
        signed_path = Path(str(built_app).replace("BrowserOS", "BrowserOS-signed"))
        artifacts.add("signed_app", signed_path, signature="abc123")
        assert artifacts.has("signed_app")

        # Step 3: Package creates DMG
        artifacts.add("dmg", Path("/out/BrowserOS.dmg"), size=50 * 1024 * 1024)
        assert artifacts.has("dmg")

        # Verify all artifacts present
        assert len(artifacts) == 3
        assert "built_app" in artifacts
        assert "signed_app" in artifacts
        assert "dmg" in artifacts

    def test_multi_architecture_build(self):
        """Test artifact management for multi-arch builds."""
        artifacts = ArtifactManager()

        # Build for multiple architectures
        artifacts.add("built_app_arm64", Path("/out/arm64/BrowserOS.app"))
        artifacts.add("built_app_x64", Path("/out/x64/BrowserOS.app"))

        # Create universal binary
        artifacts.add_multiple(
            "universal_app",
            [
                Path("/out/arm64/BrowserOS.app"),
                Path("/out/x64/BrowserOS.app"),
            ],
        )

        # Verify
        assert artifacts.has("built_app_arm64")
        assert artifacts.has("built_app_x64")
        assert artifacts.has("universal_app")

        universal_paths = artifacts.get_all("universal_app")
        assert len(universal_paths) == 2
