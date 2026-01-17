#!/usr/bin/env python3
"""
Configuration schema validation using Pydantic.

This module provides validated configuration models for the build system
using Pydantic for automatic validation, serialization, and documentation.

Example:
    config = PipelineConfig.from_file("pipeline.yaml")
    config.validate_modules_exist()  # Raises if module not registered
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from build.common.registry import ModuleRegistry


class BuildModuleConfig(BaseModel):
    """Configuration for a single build module."""

    name: str = Field(..., description="Module name (must be registered)")
    enabled: bool = Field(default=True, description="Whether module is enabled")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Module-specific parameters"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Additional module dependencies"
    )
    skip_on_platforms: list[str] = Field(
        default_factory=list, description="Platforms to skip this module on"
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Validate module name is not empty."""
        if not v or not v.strip():
            raise ValueError("Module name cannot be empty")
        return v.strip()

    @field_validator("skip_on_platforms")
    @classmethod
    def validate_platforms(cls, v: list[str]) -> list[str]:
        """Validate platform names."""
        valid_platforms = {"windows", "macos", "linux"}
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(
                    f"Invalid platform '{platform}'. Must be one of: {valid_platforms}"
                )
        return v

    def should_run_on_platform(self, platform: str) -> bool:
        """
        Check if module should run on given platform.

        Args:
            platform: Platform name (windows, macos, linux)

        Returns:
            True if module should run on platform
        """
        return self.enabled and platform not in self.skip_on_platforms


class PipelineConfig(BaseModel):
    """Configuration for a complete build pipeline."""

    name: str = Field(..., description="Pipeline name")
    description: str = Field(default="", description="Pipeline description")
    platform: Literal["windows", "macos", "linux"] = Field(
        ..., description="Target platform"
    )
    architecture: Literal["x64", "arm64", "universal"] = Field(
        ..., description="Target architecture"
    )
    build_type: Literal["debug", "release"] = Field(
        default="debug", description="Build type"
    )
    modules: list[BuildModuleConfig] = Field(
        ..., description="Modules to execute in order"
    )
    environment: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    output_dir: Optional[Path] = Field(
        default=None, description="Custom output directory"
    )
    parallel: bool = Field(
        default=False, description="Enable parallel module execution"
    )

    @field_validator("modules")
    @classmethod
    def validate_at_least_one_module(
        cls, v: list[BuildModuleConfig]
    ) -> list[BuildModuleConfig]:
        """Validate that at least one module is configured."""
        if not v:
            raise ValueError("Pipeline must have at least one module")
        return v

    @model_validator(mode="after")
    def validate_universal_only_for_macos(self) -> PipelineConfig:
        """Validate that universal architecture is only used for macOS."""
        if self.architecture == "universal" and self.platform != "macos":
            raise ValueError(
                "Universal architecture is only supported on macOS"
            )
        return self

    def validate_modules_exist(self) -> None:
        """
        Validate that all configured modules are registered.

        Raises:
            ValueError: If any module is not registered
        """
        registry = ModuleRegistry.get_instance()
        available_modules = set(registry.list_modules())

        for module_config in self.modules:
            if module_config.name not in available_modules:
                raise ValueError(
                    f"Module '{module_config.name}' is not registered. "
                    f"Available modules: {sorted(available_modules)}"
                )

    def get_enabled_modules(self) -> list[str]:
        """
        Get list of enabled module names for current platform.

        Returns:
            List of module names that should be executed
        """
        return [
            m.name
            for m in self.modules
            if m.should_run_on_platform(self.platform)
        ]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        """
        Create PipelineConfig from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Validated PipelineConfig

        Example:
            config = PipelineConfig.from_dict({
                "name": "release",
                "platform": "macos",
                "architecture": "arm64",
                "modules": [
                    {"name": "clean"},
                    {"name": "compile"},
                ]
            })
        """
        return cls(**data)

    @classmethod
    def from_file(cls, path: Path | str) -> PipelineConfig:
        """
        Load PipelineConfig from YAML or JSON file.

        Args:
            path: Path to configuration file

        Returns:
            Validated PipelineConfig

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist

        Example:
            config = PipelineConfig.from_file("pipelines/release.yaml")
        """
        import json

        try:
            import yaml

            has_yaml = True
        except ImportError:
            has_yaml = False

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        content = path.read_text()

        # Try YAML first if available
        if has_yaml and path.suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(content)
        # Fall back to JSON
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            # Try both formats
            try:
                if has_yaml:
                    data = yaml.safe_load(content)
                else:
                    data = json.loads(content)
            except Exception as e:
                raise ValueError(
                    f"Could not parse {path} as YAML or JSON: {e}"
                ) from e

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert PipelineConfig to dictionary.

        Returns:
            Dictionary representation
        """
        return self.model_dump()

    def to_file(self, path: Path | str, format: Literal["yaml", "json"] = "yaml") -> None:
        """
        Save PipelineConfig to file.

        Args:
            path: Output file path
            format: Output format (yaml or json)

        Example:
            config.to_file("output.yaml", format="yaml")
        """
        import json

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.to_dict()

        if format == "yaml":
            try:
                import yaml

                content = yaml.safe_dump(data, default_flow_style=False, sort_keys=False)
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML format. "
                    "Install with: pip install pyyaml"
                )
        else:  # json
            content = json.dumps(data, indent=2)

        path.write_text(content)


class BuildEnvironmentConfig(BaseModel):
    """Environment-specific build configuration."""

    chromium_version: str = Field(..., description="Chromium version to build")
    browseros_version: str = Field(..., description="BrowserOS version")
    build_offset: int = Field(default=5, description="Build number offset")
    enable_debug_symbols: bool = Field(
        default=True, description="Include debug symbols"
    )
    enable_proprietary_codecs: bool = Field(
        default=False, description="Include proprietary codecs"
    )
    signing_identity: Optional[str] = Field(
        default=None, description="Code signing identity"
    )
    notarization_team_id: Optional[str] = Field(
        default=None, description="Apple notarization team ID"
    )

    @field_validator("chromium_version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate version format."""
        parts = v.split(".")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid version format '{v}'. Expected MAJOR.MINOR.BUILD.PATCH"
            )
        for part in parts:
            if not part.isdigit():
                raise ValueError(
                    f"Invalid version format '{v}'. All parts must be numbers"
                )
        return v


__all__ = [
    "BuildModuleConfig",
    "PipelineConfig",
    "BuildEnvironmentConfig",
]
