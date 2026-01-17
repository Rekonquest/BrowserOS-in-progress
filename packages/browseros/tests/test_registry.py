"""Tests for build.common.registry module."""

import pytest

from build.common.module import CommandModule
from build.common.registry import (
    ModuleMetadata,
    ModuleRegistry,
    build_module,
)


class TestModuleRegistry:
    """Tests for ModuleRegistry class."""

    def setup_method(self):
        """Reset registry before each test."""
        ModuleRegistry.reset()

    def test_singleton_pattern(self):
        """Test that registry uses singleton pattern."""
        registry1 = ModuleRegistry.get_instance()
        registry2 = ModuleRegistry.get_instance()

        assert registry1 is registry2

    def test_register_module(self):
        """Test registering a module."""

        class TestModule(CommandModule):
            description = "Test module"

            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        registry.register(
            name="test",
            module_class=TestModule,
            phase="build",
            requires=["input"],
            produces=["output"],
        )

        assert registry.has("test")
        assert registry.get("test") == TestModule

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate module name raises error."""

        class TestModule1(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        class TestModule2(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        registry.register("test", TestModule1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", TestModule2)

    def test_get_metadata(self):
        """Test getting module metadata."""

        class TestModule(CommandModule):
            description = "Test module"

            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        registry.register(
            name="test",
            module_class=TestModule,
            phase="build",
            requires=["input"],
            produces=["output"],
            description="Custom description",
        )

        metadata = registry.get_metadata("test")

        assert metadata is not None
        assert metadata.name == "test"
        assert metadata.phase == "build"
        assert metadata.requires == ["input"]
        assert metadata.produces == ["output"]
        assert metadata.description == "Custom description"

    def test_get_by_phase(self):
        """Test filtering modules by phase."""

        class Module1(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        class Module2(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        registry.register("build_mod", Module1, phase="build")
        registry.register("sign_mod", Module2, phase="sign")

        build_modules = registry.get_by_phase("build")
        sign_modules = registry.get_by_phase("sign")

        assert "build_mod" in build_modules
        assert "build_mod" not in sign_modules
        assert "sign_mod" in sign_modules
        assert "sign_mod" not in build_modules

    def test_get_by_platform(self):
        """Test filtering modules by platform."""

        class MacModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        class WinModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        class UniversalModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        registry.register("mac_mod", MacModule, platform="macos")
        registry.register("win_mod", WinModule, platform="windows")
        registry.register("universal_mod", UniversalModule, platform=None)

        macos_modules = registry.get_by_platform("macos")
        windows_modules = registry.get_by_platform("windows")

        # Platform-specific modules
        assert "mac_mod" in macos_modules
        assert "mac_mod" not in windows_modules
        assert "win_mod" in windows_modules
        assert "win_mod" not in macos_modules

        # Universal modules appear on all platforms
        assert "universal_mod" in macos_modules
        assert "universal_mod" in windows_modules

    def test_list_modules(self):
        """Test listing all registered modules."""

        class Module1(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        class Module2(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        registry.register("mod1", Module1)
        registry.register("mod2", Module2)

        modules = registry.list_modules()

        assert "mod1" in modules
        assert "mod2" in modules
        assert len(modules) == 2


class TestBuildModuleDecorator:
    """Tests for @build_module decorator."""

    def setup_method(self):
        """Reset registry before each test."""
        ModuleRegistry.reset()

    def test_decorator_registers_module(self):
        """Test that decorator registers module."""

        @build_module(name="test_module", phase="build")
        class TestModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()

        assert registry.has("test_module")
        assert registry.get("test_module") == TestModule

    def test_decorator_auto_generates_name(self):
        """Test that decorator auto-generates module name from class."""

        @build_module(phase="build")
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()

        # CompileModule -> compile_module -> compile (strip _module suffix)
        assert registry.has("compile")

    def test_decorator_uses_class_attributes(self):
        """Test that decorator uses class attributes as defaults."""

        @build_module(name="test")
        class TestModule(CommandModule):
            requires = ["input"]
            produces = ["output"]
            description = "Class description"

            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        metadata = registry.get_metadata("test")

        assert metadata.requires == ["input"]
        assert metadata.produces == ["output"]
        assert metadata.description == "Class description"

    def test_decorator_explicit_overrides_class_attributes(self):
        """Test that explicit decorator args override class attributes."""

        @build_module(
            name="test",
            requires=["explicit_input"],
            produces=["explicit_output"],
            description="Explicit description",
        )
        class TestModule(CommandModule):
            requires = ["class_input"]
            produces = ["class_output"]
            description = "Class description"

            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        metadata = registry.get_metadata("test")

        # Explicit args should win
        assert metadata.requires == ["explicit_input"]
        assert metadata.produces == ["explicit_output"]
        assert metadata.description == "Explicit description"

    def test_decorator_with_platform_restriction(self):
        """Test decorator with platform restriction."""

        @build_module(name="macos_only", platform="macos")
        class MacOSModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        registry = ModuleRegistry.get_instance()
        metadata = registry.get_metadata("macos_only")

        assert metadata.platform == "macos"

    def test_decorator_preserves_class(self):
        """Test that decorator doesn't modify the class."""

        @build_module(name="test")
        class TestModule(CommandModule):
            custom_attr = "value"

            def validate(self, context):
                pass

            def execute(self, context):
                pass

        # Class should be unchanged
        assert hasattr(TestModule, "custom_attr")
        assert TestModule.custom_attr == "value"
