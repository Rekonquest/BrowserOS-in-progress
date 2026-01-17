"""Tests for build.common.platform module."""

import pytest

from build.common.platform import (
    Architecture,
    IS_LINUX,
    IS_MACOS,
    IS_WINDOWS,
    Platform,
    PlatformInfo,
    get_app_extension,
    get_executable_extension,
    get_platform,
    get_platform_arch,
)


class TestPlatform:
    """Tests for Platform enum."""

    def test_current_platform_is_valid(self):
        """Test that current platform is one of the valid platforms."""
        platform = Platform.current()
        assert platform in [Platform.WINDOWS, Platform.MACOS, Platform.LINUX]

    def test_platform_name_lower(self):
        """Test platform name in lowercase."""
        assert Platform.WINDOWS.name_lower == "windows"
        assert Platform.MACOS.name_lower == "macos"
        assert Platform.LINUX.name_lower == "linux"

    def test_platform_display_name(self):
        """Test platform display name."""
        assert Platform.WINDOWS.display_name == "Windows"
        assert Platform.MACOS.display_name == "macOS"
        assert Platform.LINUX.display_name == "Linux"

    def test_platform_is_methods(self):
        """Test platform is_* methods."""
        windows = Platform.WINDOWS
        assert windows.is_windows() is True
        assert windows.is_macos() is False
        assert windows.is_linux() is False

        macos = Platform.MACOS
        assert macos.is_windows() is False
        assert macos.is_macos() is True
        assert macos.is_linux() is False

        linux = Platform.LINUX
        assert linux.is_windows() is False
        assert linux.is_macos() is False
        assert linux.is_linux() is True


class TestArchitecture:
    """Tests for Architecture enum."""

    def test_current_architecture_is_valid(self):
        """Test that current architecture is valid."""
        arch = Architecture.current()
        assert arch in [Architecture.X64, Architecture.ARM64]

    def test_architecture_from_string(self):
        """Test parsing architecture from string."""
        assert Architecture.from_string("x64") == Architecture.X64
        assert Architecture.from_string("X64") == Architecture.X64
        assert Architecture.from_string("x86_64") == Architecture.X64
        assert Architecture.from_string("amd64") == Architecture.X64

        assert Architecture.from_string("arm64") == Architecture.ARM64
        assert Architecture.from_string("ARM64") == Architecture.ARM64
        assert Architecture.from_string("aarch64") == Architecture.ARM64

        assert Architecture.from_string("unknown") == Architecture.UNKNOWN

    def test_architecture_value(self):
        """Test architecture enum values."""
        assert Architecture.X64.value == "x64"
        assert Architecture.ARM64.value == "arm64"
        assert Architecture.UNKNOWN.value == "unknown"


class TestPlatformInfo:
    """Tests for PlatformInfo class."""

    def test_current_platform_info(self):
        """Test getting current platform info."""
        info = PlatformInfo.current()

        assert isinstance(info.platform, Platform)
        assert isinstance(info.architecture, Architecture)

    def test_executable_extension(self):
        """Test executable extension for different platforms."""
        windows_info = PlatformInfo(Platform.WINDOWS, Architecture.X64)
        assert windows_info.executable_extension == ".exe"

        macos_info = PlatformInfo(Platform.MACOS, Architecture.ARM64)
        assert macos_info.executable_extension == ""

        linux_info = PlatformInfo(Platform.LINUX, Architecture.X64)
        assert linux_info.executable_extension == ""

    def test_app_extension(self):
        """Test app extension for different platforms."""
        windows_info = PlatformInfo(Platform.WINDOWS, Architecture.X64)
        assert windows_info.app_extension == ".exe"

        macos_info = PlatformInfo(Platform.MACOS, Architecture.ARM64)
        assert macos_info.app_extension == ".app"

        linux_info = PlatformInfo(Platform.LINUX, Architecture.X64)
        assert linux_info.app_extension == ""

    def test_library_extension(self):
        """Test library extension for different platforms."""
        windows_info = PlatformInfo(Platform.WINDOWS, Architecture.X64)
        assert windows_info.library_extension == ".dll"

        macos_info = PlatformInfo(Platform.MACOS, Architecture.ARM64)
        assert macos_info.library_extension == ".dylib"

        linux_info = PlatformInfo(Platform.LINUX, Architecture.X64)
        assert linux_info.library_extension == ".so"

    def test_path_separator(self):
        """Test path separator for different platforms."""
        windows_info = PlatformInfo(Platform.WINDOWS, Architecture.X64)
        assert windows_info.path_separator == "\\"

        macos_info = PlatformInfo(Platform.MACOS, Architecture.ARM64)
        assert macos_info.path_separator == "/"

        linux_info = PlatformInfo(Platform.LINUX, Architecture.X64)
        assert linux_info.path_separator == "/"

    def test_string_representation(self):
        """Test string representation of PlatformInfo."""
        info = PlatformInfo(Platform.MACOS, Architecture.ARM64)
        str_repr = str(info)

        assert "macOS" in str_repr
        assert "arm64" in str_repr

    def test_repr(self):
        """Test developer representation of PlatformInfo."""
        info = PlatformInfo(Platform.LINUX, Architecture.X64)
        repr_str = repr(info)

        assert "PlatformInfo" in repr_str
        assert "LINUX" in repr_str
        assert "X64" in repr_str


class TestBackwardCompatibleFunctions:
    """Tests for backward-compatible helper functions."""

    def test_is_functions(self):
        """Test IS_WINDOWS, IS_MACOS, IS_LINUX functions."""
        # Exactly one should be True
        platforms = [IS_WINDOWS(), IS_MACOS(), IS_LINUX()]
        assert sum(platforms) == 1

    def test_get_platform(self):
        """Test get_platform function."""
        platform = get_platform()
        assert platform in ["windows", "macos", "linux", "unknown"]

    def test_get_platform_arch(self):
        """Test get_platform_arch function."""
        arch = get_platform_arch()
        assert arch in ["x64", "arm64", "unknown"]

    def test_get_executable_extension(self):
        """Test get_executable_extension function."""
        ext = get_executable_extension()
        if IS_WINDOWS():
            assert ext == ".exe"
        else:
            assert ext == ""

    def test_get_app_extension(self):
        """Test get_app_extension function."""
        ext = get_app_extension()
        if IS_MACOS():
            assert ext == ".app"
        elif IS_WINDOWS():
            assert ext == ".exe"
        else:
            assert ext == ""


class TestPlatformMatchCase:
    """Tests for using Platform with match/case statements (Python 3.10+)."""

    def test_match_case_pattern(self):
        """Test match/case with Platform enum."""
        platform = Platform.current()

        # Use match/case
        result = None
        match platform:
            case Platform.WINDOWS:
                result = "windows"
            case Platform.MACOS:
                result = "macos"
            case Platform.LINUX:
                result = "linux"
            case _:
                result = "unknown"

        assert result in ["windows", "macos", "linux"]
        assert result == platform.name_lower
