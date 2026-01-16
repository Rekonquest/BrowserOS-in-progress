#!/usr/bin/env python3
"""
Build configuration for BrowserOS build system.

This module provides immutable build configuration that defines
how the build should be executed.

Example:
    config = BuildConfig(
        architecture="arm64",
        build_type="release",
        platform="macos"
    )

    print(config.app_name)  # "BrowserOS.app"
    print(config.is_release)  # True
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from .platform import Platform, PlatformInfo


@dataclass(frozen=True)
class BuildConfig:
    """
    Immutable build configuration.

    Once created, this configuration cannot be modified. This ensures
    that build settings remain consistent throughout the pipeline.

    Attributes:
        platform: Target platform (windows, macos, linux)
        architecture: Target architecture (x64, arm64, universal)
        build_type: Build type (debug or release)
        app_base_name: Base application name (default: "BrowserOS")
        sparkle_version: Sparkle framework version (for macOS updates)

    Example:
        config = BuildConfig(
            platform="macos",
            architecture="arm64",
            build_type="release"
        )

        print(config.app_name)  # "BrowserOS.app"
        print(config.is_release)  # True
        print(config.is_universal)  # False

        # Cannot modify (frozen)
        # config.architecture = "x64"  # AttributeError!
    """

    platform: str
    architecture: str
    build_type: Literal["debug", "release"] = "debug"
    app_base_name: str = "BrowserOS"
    sparkle_version: str = "2.7.0"

    @classmethod
    def from_platform_info(
        cls,
        platform_info: Optional[PlatformInfo] = None,
        architecture: Optional[str] = None,
        build_type: Literal["debug", "release"] = "debug",
    ) -> BuildConfig:
        """
        Create BuildConfig from PlatformInfo.

        Args:
            platform_info: Platform information (auto-detected if None)
            architecture: Override architecture (uses platform_info if None)
            build_type: Build type

        Returns:
            BuildConfig instance

        Example:
            # Auto-detect platform
            config = BuildConfig.from_platform_info(build_type="release")

            # Explicit platform
            info = PlatformInfo.current()
            config = BuildConfig.from_platform_info(info, architecture="universal")
        """
        if platform_info is None:
            platform_info = PlatformInfo.current()

        arch = architecture or platform_info.architecture.value

        return cls(
            platform=platform_info.platform.name_lower,
            architecture=arch,
            build_type=build_type,
        )

    @property
    def is_debug(self) -> bool:
        """Check if this is a debug build."""
        return self.build_type == "debug"

    @property
    def is_release(self) -> bool:
        """Check if this is a release build."""
        return self.build_type == "release"

    @property
    def is_universal(self) -> bool:
        """Check if this is a universal (multi-arch) build."""
        return self.architecture == "universal"

    @property
    def is_windows(self) -> bool:
        """Check if building for Windows."""
        return self.platform == "windows"

    @property
    def is_macos(self) -> bool:
        """Check if building for macOS."""
        return self.platform == "macos"

    @property
    def is_linux(self) -> bool:
        """Check if building for Linux."""
        return self.platform == "linux"

    @property
    def app_name(self) -> str:
        """
        Get platform-specific application name.

        Returns:
            Application name with platform-specific extension

        Example:
            # macOS: "BrowserOS.app"
            # Windows: "BrowserOS.exe"
            # Linux: "browseros"
        """
        if self.platform == "macos":
            return f"{self.app_base_name}.app"
        elif self.platform == "windows":
            return f"{self.app_base_name}.exe"
        else:
            return self.app_base_name.lower()

    @property
    def chromium_app_name(self) -> str:
        """
        Get Chromium's default application name for this platform.

        Returns:
            Chromium app name

        Example:
            # macOS: "Chromium.app"
            # Windows: "chrome.exe"
            # Linux: "chrome"
        """
        if self.platform == "macos":
            return "Chromium.app"
        elif self.platform == "windows":
            return "chrome.exe"
        else:
            return "chrome"

    @property
    def executable_extension(self) -> str:
        """
        Get executable extension for this platform.

        Returns:
            Extension string (".exe" for Windows, "" for others)
        """
        return ".exe" if self.platform == "windows" else ""

    @property
    def app_extension(self) -> str:
        """
        Get application extension for this platform.

        Returns:
            Extension string (".app" for macOS, ".exe" for Windows, "" for Linux)
        """
        if self.platform == "macos":
            return ".app"
        elif self.platform == "windows":
            return ".exe"
        else:
            return ""

    @property
    def library_extension(self) -> str:
        """
        Get shared library extension for this platform.

        Returns:
            Extension string (".dll", ".dylib", or ".so")
        """
        if self.platform == "windows":
            return ".dll"
        elif self.platform == "macos":
            return ".dylib"
        else:
            return ".so"

    def __str__(self) -> str:
        """String representation."""
        return f"{self.platform}/{self.architecture}/{self.build_type}"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"BuildConfig(platform={self.platform!r}, "
            f"architecture={self.architecture!r}, "
            f"build_type={self.build_type!r})"
        )


__all__ = [
    "BuildConfig",
]
