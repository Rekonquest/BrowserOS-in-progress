#!/usr/bin/env python3
"""
Module dependency validation and execution ordering.

This module provides dependency graph validation and topological sorting
for build modules, ensuring they execute in the correct order.

Example:
    # Validate dependencies
    validator = DependencyValidator(["clean", "configure", "compile"])
    validator.validate()  # Raises if dependencies not met

    # Get execution order
    executor = DependencyGraph(["sign", "package"])
    execution_order = executor.topological_sort()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .registry import ModuleRegistry


class DependencyError(Exception):
    """Raised when module dependencies are not satisfied."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected."""

    pass


class MissingDependencyError(DependencyError):
    """Raised when required module or artifact is missing."""

    pass


class DependencyGraph:
    """
    Build module dependency graph.

    Manages dependencies between modules and provides topological sorting
    for correct execution order.

    Example:
        graph = DependencyGraph(registry)
        graph.add_module("compile", requires=["configured"], produces=["built_app"])
        graph.add_module("sign", requires=["built_app"], produces=["signed_app"])

        # Get execution order
        order = graph.topological_sort(["compile", "sign"])
        # Result: ["compile", "sign"]
    """

    def __init__(self, registry: ModuleRegistry):
        """
        Initialize dependency graph.

        Args:
            registry: Module registry with all available modules
        """
        self._registry = registry
        self._graph: dict[str, set[str]] = {}  # module -> dependencies
        self._producers: dict[str, str] = {}  # artifact -> module that produces it

    def add_module(self, module_name: str) -> None:
        """
        Add module to dependency graph.

        Args:
            module_name: Name of module to add

        Raises:
            ValueError: If module not found in registry
        """
        metadata = self._registry.get_metadata(module_name)
        if metadata is None:
            raise ValueError(f"Module not found in registry: {module_name}")

        # Track what this module produces
        for artifact in metadata.produces:
            if artifact in self._producers:
                raise DependencyError(
                    f"Multiple modules produce '{artifact}': "
                    f"{self._producers[artifact]} and {module_name}"
                )
            self._producers[artifact] = module_name

        # Build dependency graph
        dependencies = set()
        for required_artifact in metadata.requires:
            # Find which module produces this artifact
            if required_artifact in self._producers:
                producer = self._producers[required_artifact]
                dependencies.add(producer)

        self._graph[module_name] = dependencies

    def topological_sort(self, modules: list[str]) -> list[str]:
        """
        Perform topological sort to get execution order.

        Args:
            modules: List of module names to sort

        Returns:
            List of module names in execution order

        Raises:
            CircularDependencyError: If circular dependencies detected
            MissingDependencyError: If required dependencies missing

        Example:
            order = graph.topological_sort(["compile", "sign", "package"])
            # Returns modules in dependency order
        """
        # Add all modules to graph first
        for module_name in modules:
            if module_name not in self._graph:
                self.add_module(module_name)

        # Rebuild dependency edges now that all modules are added
        # This ensures circular dependencies are properly detected
        for module_name in modules:
            metadata = self._registry.get_metadata(module_name)
            if metadata is None:
                continue

            dependencies = set()
            for required_artifact in metadata.requires:
                if required_artifact in self._producers:
                    producer = self._producers[required_artifact]
                    if producer in modules:
                        dependencies.add(producer)

            self._graph[module_name] = dependencies

        # Kahn's algorithm for topological sort
        in_degree = {module: 0 for module in modules}

        # Calculate in-degrees
        for module in modules:
            for dependency in self._graph.get(module, set()):
                if dependency in modules:  # Only count dependencies in our set
                    in_degree[module] += 1

        # Queue of modules with no dependencies
        queue = [module for module in modules if in_degree[module] == 0]
        result = []

        while queue:
            # Sort queue for deterministic output
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # Remove current from graph
            for module in modules:
                if current in self._graph.get(module, set()):
                    in_degree[module] -= 1
                    if in_degree[module] == 0:
                        queue.append(module)

        # Check for circular dependencies
        if len(result) != len(modules):
            remaining = [m for m in modules if m not in result]
            raise CircularDependencyError(
                f"Circular dependency detected involving: {', '.join(remaining)}"
            )

        return result

    def validate_dependencies(self, modules: list[str]) -> None:
        """
        Validate that all module dependencies can be satisfied.

        Args:
            modules: List of module names to validate

        Raises:
            MissingDependencyError: If required module missing
            DependencyError: If dependencies cannot be satisfied
        """
        # Add all modules to graph
        for module_name in modules:
            if module_name not in self._graph:
                self.add_module(module_name)

        # Check that all required artifacts can be produced
        for module_name in modules:
            metadata = self._registry.get_metadata(module_name)
            if metadata is None:
                continue

            for required_artifact in metadata.requires:
                if required_artifact not in self._producers:
                    # Check if any module in the registry produces this artifact
                    # but is not included in the modules list
                    all_modules = self._registry.list_modules()
                    for other_module in all_modules:
                        other_meta = self._registry.get_metadata(other_module)
                        if other_meta and required_artifact in other_meta.produces:
                            raise MissingDependencyError(
                                f"Module '{module_name}' requires '{required_artifact}' "
                                f"produced by '{other_module}', but '{other_module}' is not included. "
                                f"Add '{other_module}' to the module list."
                            )

                    # No module in registry produces this artifact
                    raise MissingDependencyError(
                        f"Module '{module_name}' requires '{required_artifact}' "
                        f"but no module produces it. "
                        f"Available modules: {', '.join(modules)}"
                    )

                producer = self._producers[required_artifact]
                if producer not in modules:
                    raise MissingDependencyError(
                        f"Module '{module_name}' requires '{required_artifact}' "
                        f"produced by '{producer}', but '{producer}' is not included. "
                        f"Add '{producer}' to the module list."
                    )


class DependencyValidator:
    """
    Simple dependency validator for module lists.

    Validates that all dependencies are satisfied and provides execution order.

    Example:
        validator = DependencyValidator(["clean", "configure", "compile"])
        validator.validate()  # Raises if dependencies not met

        # Get execution order
        order = validator.execution_order()
    """

    def __init__(self, module_names: list[str], registry: Optional[ModuleRegistry] = None):
        """
        Initialize validator.

        Args:
            module_names: List of modules to validate
            registry: Module registry (uses global instance if None)
        """
        from .registry import ModuleRegistry as ModReg

        self._module_names = module_names
        self._registry = registry or ModReg.get_instance()
        self._graph = DependencyGraph(self._registry)

    def validate(self) -> None:
        """
        Validate all module dependencies.

        Raises:
            MissingDependencyError: If required dependencies missing
            CircularDependencyError: If circular dependencies detected
            ValueError: If module not found in registry
        """
        self._graph.validate_dependencies(self._module_names)

    def execution_order(self) -> list[str]:
        """
        Get execution order for modules.

        Returns:
            List of module names in dependency order

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        return self._graph.topological_sort(self._module_names)

    def get_missing_dependencies(self) -> dict[str, list[str]]:
        """
        Get map of modules to their missing dependencies.

        Returns:
            Dict of module name -> list of missing artifacts

        Example:
            missing = validator.get_missing_dependencies()
            # {"sign": ["built_app"], "package": ["signed_app"]}
        """
        missing = {}

        for module_name in self._module_names:
            metadata = self._registry.get_metadata(module_name)
            if metadata is None:
                continue

            module_missing = []
            for required_artifact in metadata.requires:
                # Check if any module in our list produces this
                found = False
                for other_module in self._module_names:
                    other_meta = self._registry.get_metadata(other_module)
                    if other_meta and required_artifact in other_meta.produces:
                        found = True
                        break

                if not found:
                    module_missing.append(required_artifact)

            if module_missing:
                missing[module_name] = module_missing

        return missing


__all__ = [
    "DependencyError",
    "CircularDependencyError",
    "MissingDependencyError",
    "DependencyGraph",
    "DependencyValidator",
]
