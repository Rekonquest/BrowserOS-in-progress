"""Tests for build.common.discovery module."""

from pathlib import Path

import pytest

from build.common.discovery import (
    get_module_dependencies,
    list_available_modules,
    validate_module_exists,
)
from build.common.module import CommandModule
from build.common.registry import ModuleRegistry, build_module


class TestDiscovery:
    """Tests for module discovery functions."""

    def setup_method(self):
        """Reset registry before each test."""
        ModuleRegistry.reset()

    def test_validate_module_exists(self):
        """Test checking if module exists."""

        @build_module(name="test_module")
        class TestModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        assert validate_module_exists("test_module") is True
        assert validate_module_exists("nonexistent") is False

    def test_get_module_dependencies(self):
        """Test getting module dependencies."""

        @build_module(
            name="test_module",
            requires=["input1", "input2"],
            produces=["output1", "output2"],
        )
        class TestModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        deps = get_module_dependencies("test_module")

        assert deps["requires"] == ["input1", "input2"]
        assert deps["produces"] == ["output1", "output2"]

    def test_get_module_dependencies_nonexistent(self):
        """Test getting dependencies for non-existent module."""
        deps = get_module_dependencies("nonexistent")

        assert deps["requires"] == []
        assert deps["produces"] == []

    def test_list_available_modules(self):
        """Test listing all available modules."""

        @build_module(name="module1")
        class Module1(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(name="module2")
        class Module2(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        modules = list_available_modules()

        assert "module1" in modules
        assert "module2" in modules
        assert len(modules) == 2

    def test_list_available_modules_by_phase(self):
        """Test listing modules filtered by phase."""

        @build_module(name="build_mod", phase="build")
        class BuildMod(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(name="sign_mod", phase="sign")
        class SignMod(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        build_modules = list_available_modules(phase="build")
        sign_modules = list_available_modules(phase="sign")

        assert "build_mod" in build_modules
        assert "build_mod" not in sign_modules
        assert "sign_mod" in sign_modules
        assert "sign_mod" not in build_modules

    def test_list_available_modules_by_platform(self):
        """Test listing modules filtered by platform."""

        @build_module(name="mac_mod", platform="macos")
        class MacMod(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(name="win_mod", platform="windows")
        class WinMod(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(name="universal_mod")
        class UniversalMod(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        macos_modules = list_available_modules(platform="macos")
        windows_modules = list_available_modules(platform="windows")

        # macOS platform gets mac_mod and universal_mod
        assert "mac_mod" in macos_modules
        assert "universal_mod" in macos_modules
        assert "win_mod" not in macos_modules

        # Windows platform gets win_mod and universal_mod
        assert "win_mod" in windows_modules
        assert "universal_mod" in windows_modules
        assert "mac_mod" not in windows_modules


class TestModuleNameGeneration:
    """Tests for automatic module name generation."""

    def setup_method(self):
        """Reset registry before each test."""
        ModuleRegistry.reset()

    def test_simple_name_generation(self):
        """Test simple class name to module name conversion."""

        @build_module()
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        # CompileModule -> compile_module -> compile
        assert validate_module_exists("compile")

    def test_multi_word_name_generation(self):
        """Test multi-word class name conversion."""

        @build_module()
        class GitSetupModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        # GitSetupModule -> git_setup_module -> git_setup
        assert validate_module_exists("git_setup")

    def test_acronym_name_generation(self):
        """Test acronym handling in class names."""

        @build_module()
        class DMGCreatorModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        # DMGCreatorModule -> d_m_g_creator_module -> d_m_g_creator
        assert validate_module_exists("d_m_g_creator")

    def test_explicit_name_overrides_generation(self):
        """Test that explicit name overrides auto-generation."""

        @build_module(name="custom_name")
        class SomeComplexModuleName(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        assert validate_module_exists("custom_name")
        assert not validate_module_exists("some_complex_module_name")
