#!/usr/bin/env python3
"""
Artifact management for BrowserOS build system.

This module provides a unified artifact tracking system, replacing the dual
artifact systems (dict-based and registry-based) with a single, type-safe
manager.

Example:
    artifacts = ArtifactManager()

    # Add artifacts
    artifacts.add("built_app", Path("/path/to/app"))
    artifacts.add_multiple("signed_apps", [path1, path2])

    # Get artifacts
    app_path = artifacts.get("built_app")
    all_apps = artifacts.get_all("signed_apps")

    # Check existence
    if artifacts.has("signed_app"):
        ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ArtifactMetadata:
    """
    Metadata for a build artifact.

    Attributes:
        name: Artifact identifier
        paths: List of file paths for this artifact
        size: Total size in bytes (optional)
        checksum: Checksum/hash (optional)
        signature: Digital signature (optional)
        metadata: Additional key-value metadata
    """

    name: str
    paths: list[Path] = field(default_factory=list)
    size: Optional[int] = None
    checksum: Optional[str] = None
    signature: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)

    def add_path(self, path: Path) -> None:
        """Add a path to this artifact."""
        if path not in self.paths:
            self.paths.append(path)

    @property
    def primary_path(self) -> Optional[Path]:
        """Get primary (first) path for this artifact."""
        return self.paths[0] if self.paths else None

    @property
    def path_count(self) -> int:
        """Get number of paths for this artifact."""
        return len(self.paths)


class ArtifactManager:
    """
    Unified artifact management system.

    Replaces the dual artifact systems with a single, type-safe manager.
    Supports both single and multiple artifacts per name, with optional
    metadata tracking.

    Example:
        artifacts = ArtifactManager()

        # Single artifact
        artifacts.add("built_app", Path("/path/to/app"))
        app_path = artifacts.get("built_app")

        # Multiple artifacts
        artifacts.add_multiple("arch_builds", [
            Path("/path/to/arm64"),
            Path("/path/to/x64")
        ])
        all_builds = artifacts.get_all("arch_builds")

        # With metadata
        artifacts.add(
            "signed_app",
            Path("/path/to/signed.app"),
            metadata={"signature": "abc123", "size": "1024"}
        )

        # Check existence
        if artifacts.has("signed_app"):
            print("App is signed!")
    """

    def __init__(self):
        """Initialize empty artifact manager."""
        self._artifacts: dict[str, ArtifactMetadata] = {}

    def add(
        self,
        name: str,
        path: Path,
        size: Optional[int] = None,
        checksum: Optional[str] = None,
        signature: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Add a single artifact.

        If artifact with this name already exists, the path is added to the
        existing artifact (creating a multi-path artifact).

        Args:
            name: Artifact identifier
            path: Path to artifact file
            size: File size in bytes (optional)
            checksum: Checksum/hash (optional)
            signature: Digital signature (optional)
            metadata: Additional metadata (optional)

        Example:
            artifacts.add("built_app", Path("/path/to/app"))
            artifacts.add("signed_app", Path("/path/to/signed.app"),
                         signature="abc123")
        """
        if name not in self._artifacts:
            self._artifacts[name] = ArtifactMetadata(
                name=name,
                paths=[path],
                size=size,
                checksum=checksum,
                signature=signature,
                metadata=metadata or {},
            )
        else:
            # Add to existing artifact
            self._artifacts[name].add_path(path)
            # Update metadata if provided
            if size is not None:
                self._artifacts[name].size = size
            if checksum is not None:
                self._artifacts[name].checksum = checksum
            if signature is not None:
                self._artifacts[name].signature = signature
            if metadata:
                self._artifacts[name].metadata.update(metadata)

    def add_multiple(
        self,
        name: str,
        paths: list[Path],
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Add multiple paths for a single artifact.

        Useful for artifacts that have multiple architecture variants or
        multiple output files.

        Args:
            name: Artifact identifier
            paths: List of paths
            metadata: Additional metadata (optional)

        Example:
            artifacts.add_multiple("arch_builds", [
                Path("/path/to/arm64/app"),
                Path("/path/to/x64/app")
            ])
        """
        if name not in self._artifacts:
            self._artifacts[name] = ArtifactMetadata(
                name=name, paths=list(paths), metadata=metadata or {}
            )
        else:
            for path in paths:
                self._artifacts[name].add_path(path)
            if metadata:
                self._artifacts[name].metadata.update(metadata)

    def get(self, name: str) -> Path:
        """
        Get primary path for an artifact.

        Args:
            name: Artifact identifier

        Returns:
            Primary (first) path for the artifact

        Raises:
            KeyError: If artifact not found

        Example:
            app_path = artifacts.get("built_app")
        """
        if name not in self._artifacts:
            raise KeyError(f"Artifact not found: {name}")

        primary = self._artifacts[name].primary_path
        if primary is None:
            raise ValueError(f"Artifact '{name}' has no paths")

        return primary

    def get_all(self, name: str) -> list[Path]:
        """
        Get all paths for an artifact.

        Args:
            name: Artifact identifier

        Returns:
            List of all paths for the artifact

        Raises:
            KeyError: If artifact not found

        Example:
            all_builds = artifacts.get_all("arch_builds")
        """
        if name not in self._artifacts:
            raise KeyError(f"Artifact not found: {name}")

        return self._artifacts[name].paths.copy()

    def get_metadata(self, name: str) -> ArtifactMetadata:
        """
        Get full metadata for an artifact.

        Args:
            name: Artifact identifier

        Returns:
            Complete artifact metadata

        Raises:
            KeyError: If artifact not found

        Example:
            meta = artifacts.get_metadata("signed_app")
            print(f"Signature: {meta.signature}")
        """
        if name not in self._artifacts:
            raise KeyError(f"Artifact not found: {name}")

        return self._artifacts[name]

    def has(self, name: str) -> bool:
        """
        Check if artifact exists.

        Args:
            name: Artifact identifier

        Returns:
            True if artifact registered

        Example:
            if artifacts.has("signed_app"):
                print("App is signed")
        """
        return name in self._artifacts

    def remove(self, name: str) -> None:
        """
        Remove an artifact.

        Args:
            name: Artifact identifier

        Raises:
            KeyError: If artifact not found

        Example:
            artifacts.remove("temp_artifact")
        """
        if name not in self._artifacts:
            raise KeyError(f"Artifact not found: {name}")

        del self._artifacts[name]

    def list_artifacts(self) -> list[str]:
        """
        Get list of all registered artifact names.

        Returns:
            List of artifact identifiers

        Example:
            for name in artifacts.list_artifacts():
                print(f"Artifact: {name}")
        """
        return list(self._artifacts.keys())

    def all_metadata(self) -> dict[str, ArtifactMetadata]:
        """
        Get all artifact metadata.

        Returns:
            Dict of artifact name -> metadata

        Example:
            for name, meta in artifacts.all_metadata().items():
                print(f"{name}: {meta.path_count} paths")
        """
        return self._artifacts.copy()

    def clear(self) -> None:
        """
        Clear all artifacts.

        Example:
            artifacts.clear()
        """
        self._artifacts.clear()

    def __len__(self) -> int:
        """Get number of registered artifacts."""
        return len(self._artifacts)

    def __contains__(self, name: str) -> bool:
        """Check if artifact exists (supports 'in' operator)."""
        return self.has(name)

    def __repr__(self) -> str:
        """Developer representation."""
        return f"ArtifactManager(artifacts={len(self._artifacts)})"


__all__ = [
    "ArtifactMetadata",
    "ArtifactManager",
]
