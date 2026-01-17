"""Tests for build.common.version module."""

from pathlib import Path

import pytest

from build.common.version import VersionInfo, VersionManager


class TestVersionManager:
    """Tests for VersionManager class."""

    def test_load_chromium_version(self, temp_dir):
        """Test loading Chromium version from file."""
        version_file = temp_dir / "CHROMIUM_VERSION"
        version_content = """MAJOR=137
MINOR=0
BUILD=7151
PATCH=69
"""
        version_file.write_text(version_content)

        version_mgr = VersionManager(temp_dir)

        assert version_mgr.chromium_version == "137.0.7151.69"
        assert version_mgr.chromium_major == "137"
        assert version_mgr.chromium_minor == "0"
        assert version_mgr.chromium_build == "7151"
        assert version_mgr.chromium_patch == "69"

    def test_load_browseros_build_offset(self, temp_dir):
        """Test loading BrowserOS build offset."""
        # Create directory structure
        config_dir = temp_dir / "build" / "config"
        config_dir.mkdir(parents=True)

        offset_file = config_dir / "BROWSEROS_BUILD_OFFSET"
        offset_file.write_text("5")

        version_mgr = VersionManager(temp_dir)

        assert version_mgr.browseros_build_offset == "5"

    def test_load_browseros_semantic_version(self, temp_dir):
        """Test loading BrowserOS semantic version."""
        # Create directory structure
        resources_dir = temp_dir / "build" / "resources"
        resources_dir.mkdir(parents=True)

        version_file = resources_dir / "BROWSEROS_VERSION"
        version_file.write_text("0.36.3")

        version_mgr = VersionManager(temp_dir)

        assert version_mgr.browseros_semantic_version == "0.36.3"

    def test_calculate_browseros_chromium_version(self, temp_dir):
        """Test calculating BrowserOS Chromium version with offset."""
        # Create all version files
        version_file = temp_dir / "CHROMIUM_VERSION"
        version_file.write_text("MAJOR=137\nMINOR=0\nBUILD=7151\nPATCH=69\n")

        config_dir = temp_dir / "build" / "config"
        config_dir.mkdir(parents=True)
        offset_file = config_dir / "BROWSEROS_BUILD_OFFSET"
        offset_file.write_text("5")

        version_mgr = VersionManager(temp_dir)

        # 7151 + 5 = 7156
        assert version_mgr.browseros_chromium_version == "137.0.7156.69"

    def test_explicit_chromium_version(self, temp_dir):
        """Test providing explicit Chromium version."""
        version_mgr = VersionManager(
            temp_dir, chromium_version="138.0.7200.100"
        )

        assert version_mgr.chromium_version == "138.0.7200.100"
        assert version_mgr.chromium_major == "138"
        assert version_mgr.chromium_minor == "0"
        assert version_mgr.chromium_build == "7200"
        assert version_mgr.chromium_patch == "100"

    def test_explicit_browseros_offset(self, temp_dir):
        """Test providing explicit BrowserOS offset."""
        version_mgr = VersionManager(
            temp_dir,
            chromium_version="137.0.7151.69",
            browseros_build_offset="10",
        )

        assert version_mgr.browseros_build_offset == "10"
        # 7151 + 10 = 7161
        assert version_mgr.browseros_chromium_version == "137.0.7161.69"

    def test_missing_chromium_version_file(self, temp_dir):
        """Test handling missing CHROMIUM_VERSION file."""
        version_mgr = VersionManager(temp_dir)

        assert version_mgr.chromium_version == ""
        assert version_mgr.chromium_major == ""
        assert version_mgr.browseros_chromium_version == ""

    def test_missing_offset_file(self, temp_dir):
        """Test handling missing build offset file."""
        version_mgr = VersionManager(temp_dir)

        assert version_mgr.browseros_build_offset == ""

    def test_version_info_property(self, temp_dir):
        """Test getting immutable version info."""
        version_file = temp_dir / "CHROMIUM_VERSION"
        version_file.write_text("MAJOR=137\nMINOR=0\nBUILD=7151\nPATCH=69\n")

        config_dir = temp_dir / "build" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "BROWSEROS_BUILD_OFFSET").write_text("5")

        resources_dir = temp_dir / "build" / "resources"
        resources_dir.mkdir(parents=True)
        (resources_dir / "BROWSEROS_VERSION").write_text("0.36.3")

        version_mgr = VersionManager(temp_dir)
        info = version_mgr.version_info

        assert isinstance(info, VersionInfo)
        assert info.chromium_version == "137.0.7151.69"
        assert info.browseros_chromium_version == "137.0.7156.69"
        assert info.browseros_semantic_version == "0.36.3"

    def test_version_info_immutable(self, temp_dir):
        """Test that VersionInfo is immutable."""
        version_mgr = VersionManager(
            temp_dir, chromium_version="137.0.7151.69"
        )
        info = version_mgr.version_info

        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            info.chromium_version = "999.0.0.0"

    def test_version_info_chromium_version_dict(self, temp_dir):
        """Test version_info chromium_version_dict property."""
        version_mgr = VersionManager(
            temp_dir, chromium_version="137.0.7151.69"
        )
        info = version_mgr.version_info
        version_dict = info.chromium_version_dict

        assert version_dict == {
            "MAJOR": "137",
            "MINOR": "0",
            "BUILD": "7151",
            "PATCH": "69",
        }

    def test_version_info_str_representation(self, temp_dir):
        """Test VersionInfo string representation."""
        version_mgr = VersionManager(
            temp_dir,
            chromium_version="137.0.7151.69",
            browseros_build_offset="5",
            browseros_semantic_version="0.36.3",
        )
        info = version_mgr.version_info
        str_repr = str(info)

        assert "137.0.7151.69" in str_repr
        assert "137.0.7156.69" in str_repr
        assert "0.36.3" in str_repr

    def test_invalid_chromium_version_format(self, temp_dir):
        """Test handling invalid Chromium version format."""
        version_file = temp_dir / "CHROMIUM_VERSION"
        version_file.write_text("MAJOR=137\nMINOR=0\n")  # Missing BUILD and PATCH

        version_mgr = VersionManager(temp_dir)

        # Should handle gracefully with empty values
        assert version_mgr.chromium_version == ""

    def test_parse_chromium_version_invalid_format(self, temp_dir):
        """Test parsing invalid version string."""
        # Only 3 parts instead of 4
        version_mgr = VersionManager(temp_dir, chromium_version="137.0.7151")

        # Should handle gracefully
        assert version_mgr.chromium_version == "137.0.7151"
        assert version_mgr.chromium_major == ""  # Parsing failed
