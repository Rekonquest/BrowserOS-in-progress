#!/usr/bin/env python3
"""
Platform detection and utilities.

Modern enum-based platform detection replacing the old boolean helper functions.
"""

from __future__ import annotations

import sys
import platform as platform_module
from enum import Enum, auto
from typing import Literal


class Platform(Enum):
    """
    Operating system platform enumeration.

    Use Platform.current() to get the current platform.

    Example:
        platform = Platform.current()
        if platform == Platform.MACOS:
            print("Running on macOS")

        # Or use match/case (Python 3.10+)
        match platform:
            case Platform.WINDOWS:
                ...
            case Platform.MACOS:
                ...
            case Platform.LINUX:
                ...
    """

    WINDOWS = auto()
    MACOS = auto()
    LINUX = auto()
    UNKNOWN = auto()

    @classmethod
    def current(cls) -> Platform:
        """
        Get the current platform.

        Returns:
            Platform enum for the current operating system
        """
        if sys.platform == "win32":
            return cls.WINDOWS
        elif sys.platform == "darwin":
            return cls.MACOS
        elif sys.platform.startswith("linux"):
            return cls.LINUX
        else:
            return cls.UNKNOWN

    @property
    def name_lower(self) -> str:
        """Get platform name in lowercase (windows, macos, linux)."""
        if self == Platform.WINDOWS:
            return "windows"
        elif self == Platform.MACOS:
            return "macos"
        elif self == Platform.LINUX:
            return "linux"
        else:
            return "unknown"

    @property
    def display_name(self) -> str:
        """Get platform display name (Windows, macOS, Linux)."""
        if self == Platform.WINDOWS:
            return "Windows"
        elif self == Platform.MACOS:
            return "macOS"
        elif self == Platform.LINUX:
            return "Linux"
        else:
            return "Unknown"

    def is_windows(self) -> bool:
        """Check if this platform is Windows."""
        return self == Platform.WINDOWS

    def is_macos(self) -> bool:
        """Check if this platform is macOS."""
        return self == Platform.MACOS

    def is_linux(self) -> bool:
        """Check if this platform is Linux."""
        return self == Platform.LINUX


class Architecture(Enum):
    """
    CPU architecture enumeration.

    Example:
        arch = Architecture.current()
        if arch == Architecture.ARM64:
            print("Running on ARM64")
    """

    X64 = "x64"
    ARM64 = "arm64"
    UNKNOWN = "unknown"

    @classmethod
    def current(cls) -> Architecture:
        """
        Get the current CPU architecture.

        Returns:
            Architecture enum for the current CPU
        """
        machine = platform_module.machine().lower()

        if machine in ["x86_64", "amd64"]:
            return cls.X64
        elif machine in ["aarch64", "arm64"]:
            return cls.ARM64
        else:
            return cls.UNKNOWN

    @classmethod
    def from_string(cls, arch_str: str) -> Architecture:
        """
        Parse architecture from string.

        Args:
            arch_str: Architecture string (e.g., "x64", "arm64", "x86_64")

        Returns:
            Architecture enum

        Example:
            arch = Architecture.from_string("x64")
        """
        arch_lower = arch_str.lower()

        if arch_lower in ["x64", "x86_64", "amd64"]:
            return cls.X64
        elif arch_lower in ["arm64", "aarch64"]:
            return cls.ARM64
        else:
            return cls.UNKNOWN


class PlatformInfo:
    """
    Platform information and utilities.

    This class provides platform-specific constants and utilities,
    combining platform and architecture detection.

    Example:
        info = PlatformInfo.current()
        print(f"Platform: {info.platform.display_name}")
        print(f"Architecture: {info.architecture.value}")
        print(f"Executable extension: {info.executable_extension}")
    """

    def __init__(self, platform: Platform, architecture: Architecture):
        """
        Initialize platform info.

        Args:
            platform: Platform enum
            architecture: Architecture enum
        """
        self.platform = platform
        self.architecture = architecture

    @classmethod
    def current(cls) -> PlatformInfo:
        """
        Get current platform information.

        Returns:
            PlatformInfo for the current system
        """
        return cls(Platform.current(), Architecture.current())

    @property
    def executable_extension(self) -> str:
        """Get executable file extension for this platform."""
        return ".exe" if self.platform == Platform.WINDOWS else ""

    @property
    def app_extension(self) -> str:
        """Get application bundle extension for this platform."""
        if self.platform == Platform.MACOS:
            return ".app"
        elif self.platform == Platform.WINDOWS:
            return ".exe"
        else:
            return ""

    @property
    def library_extension(self) -> str:
        """Get shared library extension for this platform."""
        if self.platform == Platform.WINDOWS:
            return ".dll"
        elif self.platform == Platform.MACOS:
            return ".dylib"
        else:
            return ".so"

    @property
    def path_separator(self) -> str:
        """Get path separator for this platform."""
        return "\\" if self.platform == Platform.WINDOWS else "/"

    def __str__(self) -> str:
        """String representation."""
        return f"{self.platform.display_name} ({self.architecture.value})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"PlatformInfo(platform={self.platform}, architecture={self.architecture})"


# =============================================================================
# Backward-compatible helper functions
# =============================================================================


def IS_WINDOWS() -> bool:
    """
    Check if running on Windows.

    DEPRECATED: Use Platform.current() == Platform.WINDOWS instead.
    """
    return Platform.current() == Platform.WINDOWS


def IS_MACOS() -> bool:
    """
    Check if running on macOS.

    DEPRECATED: Use Platform.current() == Platform.MACOS instead.
    """
    return Platform.current() == Platform.MACOS


def IS_LINUX() -> bool:
    """
    Check if running on Linux.

    DEPRECATED: Use Platform.current() == Platform.LINUX instead.
    """
    return Platform.current() == Platform.LINUX


def get_platform() -> str:
    """
    Get platform name in lowercase.

    DEPRECATED: Use Platform.current().name_lower instead.

    Returns:
        Platform name: "windows", "macos", "linux", or "unknown"
    """
    return Platform.current().name_lower


def get_platform_arch() -> str:
    """
    Get default architecture for current platform.

    DEPRECATED: Use Architecture.current().value instead.

    Returns:
        Architecture: "x64" or "arm64"
    """
    return Architecture.current().value


def get_executable_extension() -> str:
    """
    Get executable file extension for current platform.

    DEPRECATED: Use PlatformInfo.current().executable_extension instead.

    Returns:
        Extension: ".exe" for Windows, "" for others
    """
    return PlatformInfo.current().executable_extension


def get_app_extension() -> str:
    """
    Get application bundle extension for current platform.

    DEPRECATED: Use PlatformInfo.current().app_extension instead.

    Returns:
        Extension: ".app" for macOS, ".exe" for Windows, "" for Linux
    """
    return PlatformInfo.current().app_extension


__all__ = [
    # Modern API (recommended)
    "Platform",
    "Architecture",
    "PlatformInfo",
    # Backward-compatible API (deprecated but maintained)
    "IS_WINDOWS",
    "IS_MACOS",
    "IS_LINUX",
    "get_platform",
    "get_platform_arch",
    "get_executable_extension",
    "get_app_extension",
]
