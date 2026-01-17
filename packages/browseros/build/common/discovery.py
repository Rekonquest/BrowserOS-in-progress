#!/usr/bin/env python3
"""
Automatic module discovery system.

This module provides automatic discovery and loading of build modules from the
modules/ directory. Modules are discovered by scanning Python files and importing
them, which triggers their @build_module decorator registration.

Example:
    # Discover and load all modules
    discover_modules()

    # Get registry
    registry = ModuleRegistry.get_instance()
    compile_module = registry.get("compile")
"""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from pathlib import Path
from typing import Optional

from .registry import ModuleRegistry
from .utils import log_debug, log_warning


def discover_modules(
    modules_path: Optional[Path] = None, debug: bool = False
) -> ModuleRegistry:
    """
    Discover and load all build modules from the modules directory.

    This function scans the modules/ directory for Python files and imports them,
    which triggers @build_module decorator registration. Modules are discovered
    recursively through all subdirectories.

    Args:
        modules_path: Path to modules directory (auto-detected if None)
        debug: Enable debug logging

    Returns:
        ModuleRegistry instance with all discovered modules

    Example:
        registry = discover_modules()
        print(f"Discovered {len(registry.list_modules())} modules")
    """
    if modules_path is None:
        # Auto-detect modules path relative to this file
        # build/common/discovery.py -> build/modules/
        modules_path = Path(__file__).parent.parent / "modules"

    if not modules_path.exists():
        log_warning(f"Modules directory not found: {modules_path}")
        return ModuleRegistry.get_instance()

    log_debug(f"🔍 Discovering modules in: {modules_path}", enabled=debug)

    # Import all Python files in modules directory
    discovered_count = 0
    for module_info in pkgutil.walk_packages(
        [str(modules_path)], prefix="build.modules."
    ):
        try:
            # Import the module (triggers @build_module decorator)
            importlib.import_module(module_info.name)
            discovered_count += 1
            log_debug(f"  ✓ Loaded: {module_info.name}", enabled=debug)
        except ImportError as e:
            log_warning(f"  ✗ Failed to import {module_info.name}: {e}")
        except Exception as e:
            log_warning(
                f"  ✗ Error loading {module_info.name}: {e.__class__.__name__}: {e}"
            )

    registry = ModuleRegistry.get_instance()
    log_debug(
        f"✅ Discovered {len(registry.list_modules())} modules from {discovered_count} files",
        enabled=debug,
    )

    return registry


def discover_external_plugins(plugin_paths: list[Path], debug: bool = False) -> int:
    """
    Discover and load build modules from external plugin directories.

    This allows loading modules from outside the main build/modules directory,
    enabling third-party plugins and workspace-specific modules.

    Args:
        plugin_paths: List of directories to scan for modules
        debug: Enable debug logging

    Returns:
        Number of modules discovered from external plugins

    Example:
        # Load plugins from custom directory
        plugin_count = discover_external_plugins([
            Path("/workspace/custom_modules"),
            Path.home() / ".browseros/plugins"
        ])
    """
    initial_count = len(ModuleRegistry.get_instance().list_modules())

    for plugin_path in plugin_paths:
        if not plugin_path.exists():
            log_debug(f"Skipping non-existent plugin path: {plugin_path}", enabled=debug)
            continue

        log_debug(f"🔍 Discovering plugins in: {plugin_path}", enabled=debug)

        # Add plugin path to sys.path temporarily
        import sys

        if str(plugin_path) not in sys.path:
            sys.path.insert(0, str(plugin_path))

        # Discover modules in plugin directory
        for module_file in plugin_path.rglob("*.py"):
            if module_file.name.startswith("_"):
                continue

            try:
                # Import module by path
                spec = importlib.util.spec_from_file_location(
                    f"plugin.{module_file.stem}", module_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    log_debug(f"  ✓ Loaded plugin: {module_file.name}", enabled=debug)
            except Exception as e:
                log_warning(f"  ✗ Failed to load plugin {module_file}: {e}")

    final_count = len(ModuleRegistry.get_instance().list_modules())
    discovered = final_count - initial_count

    log_debug(f"✅ Discovered {discovered} external plugin modules", enabled=debug)

    return discovered


def get_module_dependencies(module_name: str) -> dict[str, list[str]]:
    """
    Get dependency information for a module.

    Args:
        module_name: Name of the module

    Returns:
        Dict with 'requires' and 'produces' lists

    Example:
        deps = get_module_dependencies("sign")
        print(f"Requires: {deps['requires']}")
        print(f"Produces: {deps['produces']}")
    """
    registry = ModuleRegistry.get_instance()
    metadata = registry.get_metadata(module_name)

    if metadata is None:
        return {"requires": [], "produces": []}

    return {"requires": metadata.requires, "produces": metadata.produces}


def validate_module_exists(module_name: str) -> bool:
    """
    Check if a module is registered.

    Args:
        module_name: Name to check

    Returns:
        True if module exists in registry

    Example:
        if validate_module_exists("compile"):
            print("Compile module is available")
    """
    return ModuleRegistry.get_instance().has(module_name)


def list_available_modules(
    phase: Optional[str] = None, platform: Optional[str] = None
) -> list[str]:
    """
    List available module names, optionally filtered.

    Args:
        phase: Filter by build phase (setup, prep, build, etc.)
        platform: Filter by platform (windows, macos, linux)

    Returns:
        List of module names

    Example:
        # All modules
        all_modules = list_available_modules()

        # Only build phase modules
        build_modules = list_available_modules(phase="build")

        # Only macOS modules
        macos_modules = list_available_modules(platform="macos")
    """
    registry = ModuleRegistry.get_instance()

    if phase is not None:
        modules = registry.get_by_phase(phase)
    elif platform is not None:
        modules = registry.get_by_platform(platform)
    else:
        modules = registry.get_all()

    return list(modules.keys())


__all__ = [
    "discover_modules",
    "discover_external_plugins",
    "get_module_dependencies",
    "validate_module_exists",
    "list_available_modules",
]
