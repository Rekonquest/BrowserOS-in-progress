"""Tests for build.common.utils module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from build.common.utils import (
    IS_LINUX,
    IS_MACOS,
    IS_WINDOWS,
    get_app_extension,
    get_executable_extension,
    get_platform,
    get_platform_arch,
    join_paths,
    normalize_path,
    safe_rmtree,
)


class TestPlatformDetection:
    """Tests for platform detection functions."""

    def test_platform_detection_mutually_exclusive(self):
        """Test that exactly one platform detection returns True."""
        platforms = [IS_WINDOWS(), IS_MACOS(), IS_LINUX()]
        assert sum(platforms) == 1, "Exactly one platform should be detected"

    @patch("sys.platform", "win32")
    def test_is_windows(self):
        """Test Windows platform detection."""
        # Need to reload the module to pick up the mocked sys.platform
        # For now, we test the actual platform
        if sys.platform == "win32":
            assert IS_WINDOWS() is True
            assert IS_MACOS() is False
            assert IS_LINUX() is False

    @patch("sys.platform", "darwin")
    def test_is_macos(self):
        """Test macOS platform detection."""
        if sys.platform == "darwin":
            assert IS_WINDOWS() is False
            assert IS_MACOS() is True
            assert IS_LINUX() is False

    @patch("sys.platform", "linux")
    def test_is_linux(self):
        """Test Linux platform detection."""
        if sys.platform.startswith("linux"):
            assert IS_WINDOWS() is False
            assert IS_MACOS() is False
            assert IS_LINUX() is True


class TestPlatformUtilities:
    """Tests for platform-specific utility functions."""

    def test_get_platform(self):
        """Test get_platform returns valid platform name."""
        platform = get_platform()
        assert platform in ["windows", "macos", "linux", "unknown"]

    def test_get_platform_arch(self):
        """Test get_platform_arch returns valid architecture."""
        arch = get_platform_arch()
        assert arch in ["x64", "arm64"]

    def test_get_executable_extension(self):
        """Test executable extension for current platform."""
        ext = get_executable_extension()
        if IS_WINDOWS():
            assert ext == ".exe"
        else:
            assert ext == ""

    def test_get_app_extension(self):
        """Test application extension for current platform."""
        ext = get_app_extension()
        if IS_MACOS():
            assert ext == ".app"
        elif IS_WINDOWS():
            assert ext == ".exe"
        else:
            assert ext == ""


class TestPathUtilities:
    """Tests for path manipulation utilities."""

    def test_normalize_path_with_string(self):
        """Test normalizing a string path."""
        result = normalize_path("/usr/local/bin")
        assert isinstance(result, Path)

    def test_normalize_path_with_path(self):
        """Test normalizing a Path object."""
        original = Path("/usr/local/bin")
        result = normalize_path(original)
        assert isinstance(result, Path)

    def test_join_paths_empty(self):
        """Test joining no paths returns empty Path."""
        result = join_paths()
        assert result == Path()

    def test_join_paths_single(self):
        """Test joining single path."""
        result = join_paths("/usr")
        assert isinstance(result, Path)

    def test_join_paths_multiple(self):
        """Test joining multiple paths."""
        result = join_paths("/usr", "local", "bin")
        assert isinstance(result, Path)
        assert str(result).replace("\\", "/").endswith("usr/local/bin")

    def test_join_paths_mixed_types(self):
        """Test joining mix of string and Path objects."""
        result = join_paths(Path("/usr"), "local", Path("bin"))
        assert isinstance(result, Path)


class TestSafeRmtree:
    """Tests for safe_rmtree utility."""

    def test_safe_rmtree_nonexistent(self):
        """Test removing non-existent directory doesn't raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "does_not_exist"
            safe_rmtree(non_existent)  # Should not raise

    def test_safe_rmtree_directory(self):
        """Test removing a directory with contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_dir"
            test_dir.mkdir()

            # Create some files
            (test_dir / "file1.txt").write_text("content1")
            (test_dir / "file2.txt").write_text("content2")

            # Create a subdirectory
            subdir = test_dir / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")

            assert test_dir.exists()

            # Remove the directory
            safe_rmtree(test_dir)

            assert not test_dir.exists()

    def test_safe_rmtree_with_string_path(self):
        """Test safe_rmtree works with string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_dir"
            test_dir.mkdir()

            safe_rmtree(str(test_dir))

            assert not test_dir.exists()
