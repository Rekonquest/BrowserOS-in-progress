#!/usr/bin/env python3
"""
Version management for BrowserOS build system.

This module provides centralized version handling, loading versions from
various files and calculating derived versions.

Example:
    version_mgr = VersionManager(root_dir)
    print(f"Chromium: {version_mgr.chromium_version}")
    print(f"BrowserOS: {version_mgr.browseros_chromium_version}")
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .utils import join_paths, log_warning


@dataclass(frozen=True)
class VersionInfo:
    """
    Immutable version information.

    Attributes:
        chromium_version: Full Chromium version (e.g., "137.0.7151.69")
        chromium_major: Major version number
        chromium_minor: Minor version number
        chromium_build: Build number
        chromium_patch: Patch number
        browseros_build_offset: BrowserOS build offset
        browseros_semantic_version: Semantic version (e.g., "0.36.3")
        browseros_chromium_version: Chromium version with offset applied
    """

    chromium_version: str
    chromium_major: str
    chromium_minor: str
    chromium_build: str
    chromium_patch: str
    browseros_build_offset: str
    browseros_semantic_version: str
    browseros_chromium_version: str

    @property
    def chromium_version_dict(self) -> dict[str, str]:
        """Get Chromium version as dictionary."""
        return {
            "MAJOR": self.chromium_major,
            "MINOR": self.chromium_minor,
            "BUILD": self.chromium_build,
            "PATCH": self.chromium_patch,
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Chromium {self.chromium_version} "
            f"→ BrowserOS {self.browseros_chromium_version} "
            f"(v{self.browseros_semantic_version})"
        )


class VersionManager:
    """
    Manages all version-related operations.

    This class loads versions from files and provides access to both
    Chromium and BrowserOS versions. It calculates derived versions
    like browseros_chromium_version automatically.

    Example:
        version_mgr = VersionManager(root_dir)
        print(version_mgr.chromium_version)  # "137.0.7151.69"
        print(version_mgr.browseros_chromium_version)  # "137.0.7156.69"

        # Get all version info
        info = version_mgr.version_info
        print(info)
    """

    def __init__(
        self,
        root_dir: Path,
        chromium_version: Optional[str] = None,
        browseros_build_offset: Optional[str] = None,
        browseros_semantic_version: Optional[str] = None,
    ):
        """
        Initialize version manager.

        Args:
            root_dir: Root directory of the build
            chromium_version: Override Chromium version (or load from file)
            browseros_build_offset: Override build offset (or load from file)
            browseros_semantic_version: Override semantic version (or load from file)
        """
        self._root_dir = root_dir

        # Load Chromium version
        if chromium_version is None:
            self._chromium_version, self._version_dict = self._load_chromium_version(
                root_dir
            )
        else:
            self._chromium_version = chromium_version
            self._version_dict = self._parse_chromium_version(chromium_version)

        # Load BrowserOS build offset
        if browseros_build_offset is None:
            self._browseros_build_offset = self._load_browseros_build_offset(root_dir)
        else:
            self._browseros_build_offset = browseros_build_offset

        # Load semantic version
        if browseros_semantic_version is None:
            self._browseros_semantic_version = self._load_semantic_version(root_dir)
        else:
            self._browseros_semantic_version = browseros_semantic_version

        # Calculate BrowserOS Chromium version
        self._browseros_chromium_version = self._calculate_browseros_chromium_version()

    @property
    def chromium_version(self) -> str:
        """Get Chromium version string (e.g., "137.0.7151.69")."""
        return self._chromium_version

    @property
    def chromium_major(self) -> str:
        """Get Chromium major version."""
        return self._version_dict.get("MAJOR", "")

    @property
    def chromium_minor(self) -> str:
        """Get Chromium minor version."""
        return self._version_dict.get("MINOR", "")

    @property
    def chromium_build(self) -> str:
        """Get Chromium build number."""
        return self._version_dict.get("BUILD", "")

    @property
    def chromium_patch(self) -> str:
        """Get Chromium patch number."""
        return self._version_dict.get("PATCH", "")

    @property
    def browseros_build_offset(self) -> str:
        """Get BrowserOS build offset."""
        return self._browseros_build_offset

    @property
    def browseros_semantic_version(self) -> str:
        """Get BrowserOS semantic version (e.g., "0.36.3")."""
        return self._browseros_semantic_version

    @property
    def browseros_chromium_version(self) -> str:
        """Get BrowserOS Chromium version with offset applied."""
        return self._browseros_chromium_version

    @property
    def version_info(self) -> VersionInfo:
        """Get immutable version information object."""
        return VersionInfo(
            chromium_version=self._chromium_version,
            chromium_major=self.chromium_major,
            chromium_minor=self.chromium_minor,
            chromium_build=self.chromium_build,
            chromium_patch=self.chromium_patch,
            browseros_build_offset=self._browseros_build_offset,
            browseros_semantic_version=self._browseros_semantic_version,
            browseros_chromium_version=self._browseros_chromium_version,
        )

    def _calculate_browseros_chromium_version(self) -> str:
        """
        Calculate BrowserOS Chromium version.

        Takes the Chromium BUILD number and adds the BrowserOS build offset.

        Returns:
            Version string like "137.0.7156.69" (7151 + 5 = 7156)
        """
        if not self._chromium_version or not self._browseros_build_offset:
            return ""

        if not self._version_dict:
            return ""

        try:
            # Calculate new BUILD number by adding offset
            original_build = int(self._version_dict["BUILD"])
            offset = int(self._browseros_build_offset)
            new_build = original_build + offset

            # Construct new version string
            return f"{self._version_dict['MAJOR']}.{self._version_dict['MINOR']}.{new_build}.{self._version_dict['PATCH']}"
        except (ValueError, KeyError) as e:
            log_warning(
                f"Failed to calculate BrowserOS Chromium version: {e}"
            )
            return ""

    @staticmethod
    def _load_chromium_version(root_dir: Path) -> tuple[str, dict[str, str]]:
        """
        Load Chromium version from CHROMIUM_VERSION file.

        Args:
            root_dir: Root directory containing CHROMIUM_VERSION

        Returns:
            Tuple of (version_string, version_dict)

        Example:
            ("137.0.7151.69", {"MAJOR": "137", "MINOR": "0", ...})
        """
        version_dict: dict[str, str] = {}
        version_file = join_paths(root_dir, "CHROMIUM_VERSION")

        if not version_file.exists():
            log_warning(f"CHROMIUM_VERSION file not found: {version_file}")
            return "", version_dict

        try:
            # Parse VERSION file format: MAJOR=137\nMINOR=0\nBUILD=7151\nPATCH=69
            for line in version_file.read_text().strip().split("\n"):
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                version_dict[key.strip()] = value.strip()

            # Validate all required keys present
            required_keys = {"MAJOR", "MINOR", "BUILD", "PATCH"}
            if not required_keys.issubset(version_dict.keys()):
                missing = required_keys - version_dict.keys()
                log_warning(
                    f"CHROMIUM_VERSION missing keys: {missing}"
                )
                return "", {}

            # Construct chromium_version as MAJOR.MINOR.BUILD.PATCH
            chromium_version = (
                f"{version_dict['MAJOR']}.{version_dict['MINOR']}."
                f"{version_dict['BUILD']}.{version_dict['PATCH']}"
            )
            return chromium_version, version_dict

        except Exception as e:
            log_warning(f"Failed to load CHROMIUM_VERSION: {e}")
            return "", {}

    @staticmethod
    def _parse_chromium_version(version_str: str) -> dict[str, str]:
        """
        Parse Chromium version string into components.

        Args:
            version_str: Version string like "137.0.7151.69"

        Returns:
            Dict with MAJOR, MINOR, BUILD, PATCH keys
        """
        try:
            parts = version_str.split(".")
            if len(parts) != 4:
                log_warning(
                    f"Invalid Chromium version format: {version_str} (expected MAJOR.MINOR.BUILD.PATCH)"
                )
                return {}

            return {
                "MAJOR": parts[0],
                "MINOR": parts[1],
                "BUILD": parts[2],
                "PATCH": parts[3],
            }
        except Exception as e:
            log_warning(f"Failed to parse Chromium version: {e}")
            return {}

    @staticmethod
    def _load_browseros_build_offset(root_dir: Path) -> str:
        """
        Load BrowserOS build offset from config/BROWSEROS_BUILD_OFFSET.

        Args:
            root_dir: Root directory

        Returns:
            Build offset string (e.g., "5")
        """
        version_file = join_paths(root_dir, "build", "config", "BROWSEROS_BUILD_OFFSET")

        if not version_file.exists():
            log_warning(
                f"BROWSEROS_BUILD_OFFSET file not found: {version_file}"
            )
            return ""

        try:
            return version_file.read_text().strip()
        except Exception as e:
            log_warning(f"Failed to load BROWSEROS_BUILD_OFFSET: {e}")
            return ""

    @staticmethod
    def _load_semantic_version(root_dir: Path) -> str:
        """
        Load semantic version from resources/BROWSEROS_VERSION.

        Args:
            root_dir: Root directory

        Returns:
            Semantic version string (e.g., "0.36.3")
        """
        version_file = join_paths(root_dir, "build", "resources", "BROWSEROS_VERSION")

        if not version_file.exists():
            log_warning(
                f"BROWSEROS_VERSION file not found: {version_file}"
            )
            return ""

        try:
            return version_file.read_text().strip()
        except Exception as e:
            log_warning(f"Failed to load BROWSEROS_VERSION: {e}")
            return ""


__all__ = [
    "VersionInfo",
    "VersionManager",
]
