#!/usr/bin/env python3
"""
Path management for BrowserOS build system.

This module provides centralized path resolution and construction,
keeping all path-related logic in one place.

IMPORTANT: get_package_root() has NO local imports to avoid circular dependencies.
It is imported by both context.py and env.py at module load time.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .platform import PlatformInfo


@lru_cache(maxsize=1)
def get_package_root() -> Path:
    """Find browseros package root by walking up looking for pyproject.toml.

    Walks up from this file's location looking for a pyproject.toml that
    contains the browseros package definition.

    Returns:
        Path to the browseros package root (e.g., packages/browseros/)

    Raises:
        RuntimeError: If package root cannot be found
    """
    current = Path(__file__).resolve().parent

    while current != current.parent:
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            # Match name = "browseros" with flexible whitespace
            if re.search(r'^name\s*=\s*["\']browseros["\']', content, re.MULTILINE):
                return current
        current = current.parent

    raise RuntimeError(
        "Could not find browseros package root. "
        "Expected to find pyproject.toml with name = 'browseros' "
        f"in ancestors of {Path(__file__).resolve()}"
    )


class PathManager:
    """
    Centralized path management.

    Handles all path resolution and construction logic. Paths are validated
    on access where appropriate.

    Example:
        paths = PathManager(
            root_dir=Path("/workspace/BrowserOS"),
            chromium_src=Path("/workspace/chromium/src")
        )

        print(paths.chromium_src)      # /workspace/chromium/src
        print(paths.out_dir_path)      # /workspace/chromium/src/out/Default_x64
        print(paths.build_tools_dir)   # /workspace/BrowserOS/build
    """

    def __init__(
        self,
        root_dir: Optional[Path] = None,
        chromium_src: Optional[Path] = None,
        out_dir: str = "out/Default",
        architecture: Optional[str] = None,
    ):
        """
        Initialize path manager.

        Args:
            root_dir: BrowserOS root directory (auto-detected if None)
            chromium_src: Chromium source directory
            out_dir: Output directory name (relative to chromium_src)
            architecture: Build architecture (x64, arm64, etc.)
        """
        self._root_dir = root_dir or get_package_root()
        self._chromium_src = chromium_src or Path()
        self._out_dir = out_dir
        self._architecture = architecture

    @property
    def root_dir(self) -> Path:
        """Get BrowserOS root directory."""
        return self._root_dir

    @property
    def chromium_src(self) -> Path:
        """Get Chromium source directory."""
        return self._chromium_src

    @chromium_src.setter
    def chromium_src(self, value: Path) -> None:
        """Set Chromium source directory."""
        self._chromium_src = value

    @property
    def out_dir(self) -> str:
        """Get output directory name (e.g., 'out/Default_x64')."""
        return self._out_dir

    @out_dir.setter
    def out_dir(self, value: str) -> None:
        """Set output directory name."""
        self._out_dir = value

    @property
    def out_dir_path(self) -> Path:
        """
        Get full output directory path.

        Returns:
            Full path to output directory (chromium_src/out/Default_x64)
        """
        return self._chromium_src / self._out_dir

    @property
    def build_dir(self) -> Path:
        """Get build tools directory (build/)."""
        return self._root_dir / "build"

    @property
    def build_config_dir(self) -> Path:
        """Get build/config directory."""
        return self.build_dir / "config"

    @property
    def build_resources_dir(self) -> Path:
        """Get build/resources directory."""
        return self.build_dir / "resources"

    @property
    def build_modules_dir(self) -> Path:
        """Get build/modules directory."""
        return self.build_dir / "modules"

    @property
    def logs_dir(self) -> Path:
        """Get logs directory."""
        logs = self._root_dir / "logs"
        logs.mkdir(exist_ok=True)
        return logs

    def get_gn_flags_file(
        self, platform: str, architecture: Optional[str] = None, build_type: str = "debug"
    ) -> Path:
        """
        Get GN args file for specific configuration.

        Args:
            platform: Platform name (windows, macos, linux)
            architecture: Build architecture (uses self._architecture if None)
            build_type: Build type (debug or release)

        Returns:
            Path to GN args file
        """
        arch = architecture or self._architecture or "x64"
        filename = f"{platform}_{arch}_{build_type}.gn"
        return self.build_config_dir / "gn_args" / filename

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"PathManager(root={self._root_dir}, "
            f"chromium_src={self._chromium_src}, "
            f"out_dir={self._out_dir})"
        )


__all__ = [
    "get_package_root",
    "PathManager",
]
