"""Tests for build.common.dependencies module."""

import pytest

from build.common.dependencies import (
    CircularDependencyError,
    DependencyError,
    DependencyGraph,
    DependencyValidator,
    MissingDependencyError,
)
from build.common.module import CommandModule
from build.common.registry import ModuleRegistry, build_module


class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    def setup_method(self):
        """Reset registry before each test."""
        ModuleRegistry.reset()

    def test_add_module(self):
        """Test adding module to dependency graph."""

        @build_module(
            name="test_module",
            requires=["input1"],
            produces=["output1"],
        )
        class TestModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        graph.add_module("test_module")
        assert "test_module" in graph._graph

    def test_add_module_not_found(self):
        """Test adding non-existent module raises error."""
        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        with pytest.raises(ValueError, match="Module not found"):
            graph.add_module("nonexistent")

    def test_duplicate_artifact_producers(self):
        """Test that multiple modules producing same artifact raises error."""

        @build_module(
            name="module1",
            produces=["output1"],
        )
        class Module1(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="module2",
            produces=["output1"],  # Same artifact
        )
        class Module2(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        graph.add_module("module1")

        with pytest.raises(DependencyError, match="Multiple modules produce"):
            graph.add_module("module2")

    def test_topological_sort_simple(self):
        """Test topological sort with simple dependency chain."""

        @build_module(name="clean", produces=["clean_workspace"])
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="configure",
            requires=["clean_workspace"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="compile",
            requires=["configured"],
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        order = graph.topological_sort(["clean", "configure", "compile"])

        # Should be in dependency order
        assert order.index("clean") < order.index("configure")
        assert order.index("configure") < order.index("compile")

    def test_topological_sort_parallel_modules(self):
        """Test topological sort with parallel independent modules."""

        @build_module(name="module_a", produces=["artifact_a"])
        class ModuleA(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(name="module_b", produces=["artifact_b"])
        class ModuleB(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="module_c",
            requires=["artifact_a", "artifact_b"],
            produces=["artifact_c"],
        )
        class ModuleC(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        order = graph.topological_sort(["module_a", "module_b", "module_c"])

        # Both module_a and module_b should come before module_c
        assert order.index("module_a") < order.index("module_c")
        assert order.index("module_b") < order.index("module_c")

    def test_topological_sort_circular_dependency(self):
        """Test that circular dependencies are detected."""

        @build_module(
            name="module_a",
            requires=["artifact_b"],
            produces=["artifact_a"],
        )
        class ModuleA(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="module_b",
            requires=["artifact_a"],
            produces=["artifact_b"],
        )
        class ModuleB(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        with pytest.raises(CircularDependencyError, match="Circular dependency"):
            graph.topological_sort(["module_a", "module_b"])

    def test_validate_dependencies_success(self):
        """Test successful dependency validation."""

        @build_module(name="clean", produces=["clean_workspace"])
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="configure",
            requires=["clean_workspace"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        # Should not raise
        graph.validate_dependencies(["clean", "configure"])

    def test_validate_dependencies_missing_producer(self):
        """Test validation fails when required artifact has no producer."""

        @build_module(
            name="compile",
            requires=["configured"],  # No module produces this
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        with pytest.raises(
            MissingDependencyError, match="requires 'configured' but no module produces it"
        ):
            graph.validate_dependencies(["compile"])

    def test_validate_dependencies_missing_module(self):
        """Test validation fails when producer module not included."""

        @build_module(name="configure", produces=["configured"])
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="compile",
            requires=["configured"],
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        graph = DependencyGraph(registry)

        with pytest.raises(
            MissingDependencyError, match="'configure' is not included"
        ):
            graph.validate_dependencies(["compile"])  # Missing configure


class TestDependencyValidator:
    """Tests for DependencyValidator class."""

    def setup_method(self):
        """Reset registry before each test."""
        ModuleRegistry.reset()

    def test_validate_success(self):
        """Test successful validation."""

        @build_module(name="clean", produces=["clean_workspace"])
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="configure",
            requires=["clean_workspace"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        validator = DependencyValidator(["clean", "configure"])

        # Should not raise
        validator.validate()

    def test_validate_missing_dependency(self):
        """Test validation fails with missing dependency."""

        @build_module(
            name="compile",
            requires=["configured"],
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        validator = DependencyValidator(["compile"])

        with pytest.raises(MissingDependencyError):
            validator.validate()

    def test_execution_order(self):
        """Test getting execution order."""

        @build_module(name="clean", produces=["clean_workspace"])
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="configure",
            requires=["clean_workspace"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="compile",
            requires=["configured"],
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        validator = DependencyValidator(["clean", "configure", "compile"])
        order = validator.execution_order()

        assert order == ["clean", "configure", "compile"]

    def test_get_missing_dependencies(self):
        """Test getting map of missing dependencies."""

        @build_module(name="clean", produces=["clean_workspace"])
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="compile",
            requires=["configured", "clean_workspace"],
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="sign",
            requires=["built_app", "signing_cert"],
            produces=["signed_app"],
        )
        class SignModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        validator = DependencyValidator(["clean", "compile", "sign"])
        missing = validator.get_missing_dependencies()

        # compile is missing 'configured' (clean_workspace is satisfied)
        assert "compile" in missing
        assert "configured" in missing["compile"]
        assert "clean_workspace" not in missing["compile"]

        # sign is missing 'signing_cert' (built_app is satisfied)
        assert "sign" in missing
        assert "signing_cert" in missing["sign"]
        assert "built_app" not in missing["sign"]

    def test_get_missing_dependencies_none(self):
        """Test get_missing_dependencies returns empty dict when all satisfied."""

        @build_module(name="clean", produces=["clean_workspace"])
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="configure",
            requires=["clean_workspace"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        validator = DependencyValidator(["clean", "configure"])
        missing = validator.get_missing_dependencies()

        assert missing == {}

    def test_complex_dependency_graph(self):
        """Test complex multi-level dependency graph."""

        @build_module(name="init", produces=["initialized"])
        class InitModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="fetch",
            requires=["initialized"],
            produces=["source_code"],
        )
        class FetchModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="patch",
            requires=["source_code"],
            produces=["patched_source"],
        )
        class PatchModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="configure",
            requires=["patched_source"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="compile",
            requires=["configured"],
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="sign",
            requires=["built_app"],
            produces=["signed_app"],
        )
        class SignModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="package",
            requires=["signed_app"],
            produces=["installer"],
        )
        class PackageModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        validator = DependencyValidator(
            ["init", "fetch", "patch", "configure", "compile", "sign", "package"]
        )

        # Validate all dependencies
        validator.validate()

        # Get execution order
        order = validator.execution_order()

        # Verify correct order
        expected = ["init", "fetch", "patch", "configure", "compile", "sign", "package"]
        assert order == expected
