#!/usr/bin/env python3
"""
Module registry system with auto-discovery.

This module provides a decorator-based registration system for build modules,
enabling plugin-style architecture where modules can self-register without
requiring modifications to core build files.

Example:
    @build_module(
        name="compile",
        phase="build",
        requires=["configured"],
        produces=["built_app"],
        description="Compile Chromium sources"
    )
    class CompileModule(CommandModule):
        def validate(self, context):
            ...
        def execute(self, context):
            ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, Type

if TYPE_CHECKING:
    from .module import CommandModule


@dataclass
class ModuleMetadata:
    """
    Metadata for a registered build module.

    Attributes:
        name: Unique module identifier
        module_class: The CommandModule class
        phase: Build phase (setup, prep, build, sign, package, upload)
        requires: List of artifact names this module needs
        produces: List of artifact names this module creates
        description: Human-readable description
        platform: Platform restriction (None = all platforms)
        enabled_by_default: Whether module runs in standard build
    """

    name: str
    module_class: Type[CommandModule]
    phase: str = "build"
    requires: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    description: str = "No description provided"
    platform: Optional[str] = None  # "windows", "macos", "linux", or None for all
    enabled_by_default: bool = True


class ModuleRegistry:
    """
    Central registry for build modules.

    Modules can be registered using the @build_module decorator or manually
    via register_module(). The registry supports:
    - Auto-discovery from modules directory
    - Platform-specific filtering
    - Dependency validation
    - Module lookup by name or phase

    Example:
        # Register module
        @build_module(name="compile", phase="build")
        class CompileModule(CommandModule):
            ...

        # Get module
        registry = ModuleRegistry.get_instance()
        module_class = registry.get("compile")
    """

    _instance: Optional[ModuleRegistry] = None
    _modules: dict[str, ModuleMetadata]

    def __init__(self):
        """Initialize empty registry."""
        self._modules = {}

    @classmethod
    def get_instance(cls) -> ModuleRegistry:
        """Get singleton registry instance."""
        if cls._instance is None:
            cls._instance = ModuleRegistry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset registry (mainly for testing)."""
        cls._instance = None

    def register(
        self,
        name: str,
        module_class: Type[CommandModule],
        phase: str = "build",
        requires: Optional[list[str]] = None,
        produces: Optional[list[str]] = None,
        description: Optional[str] = None,
        platform: Optional[str] = None,
        enabled_by_default: bool = True,
    ) -> None:
        """
        Register a module with the registry.

        Args:
            name: Unique module identifier
            module_class: The CommandModule class
            phase: Build phase (setup, prep, build, sign, package, upload)
            requires: Artifact dependencies
            produces: Artifacts created by this module
            description: Human-readable description
            platform: Platform restriction (windows/macos/linux or None for all)
            enabled_by_default: Whether module runs in standard builds

        Raises:
            ValueError: If module name already registered
        """
        if name in self._modules:
            existing = self._modules[name]
            raise ValueError(
                f"Module '{name}' already registered by {existing.module_class.__name__}"
            )

        # Use module class attributes as defaults if not specified
        if requires is None:
            requires = getattr(module_class, "requires", [])
        if produces is None:
            produces = getattr(module_class, "produces", [])
        if description is None:
            description = getattr(module_class, "description", "No description provided")

        metadata = ModuleMetadata(
            name=name,
            module_class=module_class,
            phase=phase,
            requires=requires,
            produces=produces,
            description=description,
            platform=platform,
            enabled_by_default=enabled_by_default,
        )

        self._modules[name] = metadata

    def get(self, name: str) -> Optional[Type[CommandModule]]:
        """
        Get module class by name.

        Args:
            name: Module name

        Returns:
            Module class or None if not found
        """
        metadata = self._modules.get(name)
        return metadata.module_class if metadata else None

    def get_metadata(self, name: str) -> Optional[ModuleMetadata]:
        """
        Get module metadata by name.

        Args:
            name: Module name

        Returns:
            ModuleMetadata or None if not found
        """
        return self._modules.get(name)

    def get_all(self) -> dict[str, ModuleMetadata]:
        """Get all registered modules."""
        return self._modules.copy()

    def get_by_phase(self, phase: str) -> dict[str, ModuleMetadata]:
        """
        Get all modules for a specific phase.

        Args:
            phase: Build phase name

        Returns:
            Dict of module name -> metadata for all modules in phase
        """
        return {
            name: meta for name, meta in self._modules.items() if meta.phase == phase
        }

    def get_by_platform(
        self, platform: str
    ) -> dict[str, ModuleMetadata]:
        """
        Get all modules compatible with a platform.

        Args:
            platform: Platform name (windows, macos, linux)

        Returns:
            Dict of module name -> metadata for compatible modules
        """
        return {
            name: meta
            for name, meta in self._modules.items()
            if meta.platform is None or meta.platform == platform
        }

    def has(self, name: str) -> bool:
        """Check if module is registered."""
        return name in self._modules

    def list_modules(self) -> list[str]:
        """Get list of all registered module names."""
        return list(self._modules.keys())

    def list_phases(self) -> list[str]:
        """Get list of all registered phases."""
        phases = {meta.phase for meta in self._modules.values()}
        # Return in standard order
        standard_order = ["setup", "prep", "build", "sign", "package", "upload"]
        return [p for p in standard_order if p in phases] + sorted(
            phases - set(standard_order)
        )


# Global registry decorator
def build_module(
    name: Optional[str] = None,
    phase: str = "build",
    requires: Optional[list[str]] = None,
    produces: Optional[list[str]] = None,
    description: Optional[str] = None,
    platform: Optional[str] = None,
    enabled_by_default: bool = True,
) -> Callable[[Type[CommandModule]], Type[CommandModule]]:
    """
    Decorator to register a module with the global registry.

    This decorator allows modules to self-register without modifying core files.
    The module is automatically registered when the module file is imported.

    Args:
        name: Module name (defaults to class name in snake_case)
        phase: Build phase (setup, prep, build, sign, package, upload)
        requires: Artifacts needed by this module
        produces: Artifacts created by this module
        description: Human-readable description
        platform: Platform restriction (windows/macos/linux or None)
        enabled_by_default: Whether module runs in standard builds

    Returns:
        Decorator function that registers the class

    Example:
        @build_module(
            name="compile",
            phase="build",
            requires=["configured"],
            produces=["built_app"],
            description="Compile Chromium sources"
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                ...
            def execute(self, context):
                ...
    """

    def decorator(cls: Type[CommandModule]) -> Type[CommandModule]:
        # Auto-generate name from class if not provided
        module_name = name
        if module_name is None:
            # Convert ClassName to class_name
            module_name = "".join(
                ["_" + c.lower() if c.isupper() else c for c in cls.__name__]
            ).lstrip("_")
            # Remove _module suffix if present
            if module_name.endswith("_module"):
                module_name = module_name[:-7]

        # Register with global registry
        registry = ModuleRegistry.get_instance()
        registry.register(
            name=module_name,
            module_class=cls,
            phase=phase,
            requires=requires,
            produces=produces,
            description=description,
            platform=platform,
            enabled_by_default=enabled_by_default,
        )

        return cls

    return decorator


__all__ = [
    "ModuleMetadata",
    "ModuleRegistry",
    "build_module",
]
