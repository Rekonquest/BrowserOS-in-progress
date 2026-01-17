"""Tests for build.common.config_schema module."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from build.common.config_schema import (
    BuildEnvironmentConfig,
    BuildModuleConfig,
    PipelineConfig,
)
from build.common.registry import ModuleRegistry, build_module
from build.common.module import CommandModule


class TestBuildModuleConfig:
    """Tests for BuildModuleConfig."""

    def test_create_module_config(self):
        """Test creating a module configuration."""
        config = BuildModuleConfig(name="test_module")

        assert config.name == "test_module"
        assert config.enabled is True
        assert config.parameters == {}
        assert config.depends_on == []

    def test_module_config_with_parameters(self):
        """Test module config with custom parameters."""
        config = BuildModuleConfig(
            name="compile",
            enabled=True,
            parameters={"threads": 8, "verbose": True},
            depends_on=["configure"],
        )

        assert config.parameters["threads"] == 8
        assert config.depends_on == ["configure"]

    def test_empty_module_name_rejected(self):
        """Test that empty module name is rejected."""
        with pytest.raises(ValidationError):
            BuildModuleConfig(name="")

    def test_skip_on_platforms(self):
        """Test platform skipping."""
        config = BuildModuleConfig(
            name="sign",
            skip_on_platforms=["linux", "windows"],
        )

        assert not config.should_run_on_platform("linux")
        assert not config.should_run_on_platform("windows")
        assert config.should_run_on_platform("macos")

    def test_invalid_platform_rejected(self):
        """Test that invalid platform names are rejected."""
        with pytest.raises(ValidationError, match="Invalid platform"):
            BuildModuleConfig(
                name="test",
                skip_on_platforms=["invalid_platform"],
            )

    def test_disabled_module(self):
        """Test disabled module."""
        config = BuildModuleConfig(name="test", enabled=False)

        assert not config.should_run_on_platform("macos")
        assert not config.should_run_on_platform("linux")


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_create_pipeline_config(self):
        """Test creating a pipeline configuration."""
        config = PipelineConfig(
            name="release",
            platform="macos",
            architecture="arm64",
            modules=[
                BuildModuleConfig(name="clean"),
                BuildModuleConfig(name="compile"),
            ],
        )

        assert config.name == "release"
        assert config.platform == "macos"
        assert config.architecture == "arm64"
        assert len(config.modules) == 2

    def test_empty_modules_rejected(self):
        """Test that empty modules list is rejected."""
        with pytest.raises(ValidationError, match="at least one module"):
            PipelineConfig(
                name="test",
                platform="macos",
                architecture="arm64",
                modules=[],
            )

    def test_invalid_platform_rejected(self):
        """Test that invalid platform is rejected."""
        with pytest.raises(ValidationError):
            PipelineConfig(
                name="test",
                platform="invalid",  # type: ignore
                architecture="x64",
                modules=[BuildModuleConfig(name="test")],
            )

    def test_universal_only_for_macos(self):
        """Test that universal architecture requires macOS."""
        # Should work for macOS
        config = PipelineConfig(
            name="test",
            platform="macos",
            architecture="universal",
            modules=[BuildModuleConfig(name="test")],
        )
        assert config.architecture == "universal"

        # Should fail for other platforms
        with pytest.raises(
            ValidationError, match="Universal architecture is only supported on macOS"
        ):
            PipelineConfig(
                name="test",
                platform="linux",
                architecture="universal",
                modules=[BuildModuleConfig(name="test")],
            )

    def test_validate_modules_exist(self, reset_registry):
        """Test validating that modules are registered."""

        @build_module(name="test_module")
        class TestModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        config = PipelineConfig(
            name="test",
            platform="macos",
            architecture="arm64",
            modules=[BuildModuleConfig(name="test_module")],
        )

        # Should not raise
        config.validate_modules_exist()

        # Should raise for non-existent module
        config2 = PipelineConfig(
            name="test",
            platform="macos",
            architecture="arm64",
            modules=[BuildModuleConfig(name="nonexistent")],
        )

        with pytest.raises(ValueError, match="not registered"):
            config2.validate_modules_exist()

    def test_get_enabled_modules(self):
        """Test getting enabled modules for platform."""
        config = PipelineConfig(
            name="test",
            platform="macos",
            architecture="arm64",
            modules=[
                BuildModuleConfig(name="module1"),
                BuildModuleConfig(name="module2", enabled=False),
                BuildModuleConfig(name="module3", skip_on_platforms=["macos"]),
                BuildModuleConfig(name="module4"),
            ],
        )

        enabled = config.get_enabled_modules()

        assert "module1" in enabled
        assert "module2" not in enabled  # Disabled
        assert "module3" not in enabled  # Skipped on macOS
        assert "module4" in enabled

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "name": "release",
            "platform": "macos",
            "architecture": "arm64",
            "build_type": "release",
            "modules": [
                {"name": "clean"},
                {"name": "compile", "parameters": {"threads": 8}},
            ],
        }

        config = PipelineConfig.from_dict(data)

        assert config.name == "release"
        assert config.build_type == "release"
        assert len(config.modules) == 2
        assert config.modules[1].parameters["threads"] == 8

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = PipelineConfig(
            name="test",
            platform="macos",
            architecture="arm64",
            modules=[BuildModuleConfig(name="test")],
        )

        data = config.to_dict()

        assert data["name"] == "test"
        assert data["platform"] == "macos"
        assert isinstance(data, dict)

    def test_from_json_file(self, tmp_path):
        """Test loading config from JSON file."""
        config_file = tmp_path / "config.json"
        data = {
            "name": "test",
            "platform": "macos",
            "architecture": "arm64",
            "modules": [{"name": "clean"}],
        }
        config_file.write_text(json.dumps(data))

        config = PipelineConfig.from_file(config_file)

        assert config.name == "test"
        assert config.platform == "macos"

    def test_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            PipelineConfig.from_file("nonexistent.yaml")

    def test_to_json_file(self, tmp_path):
        """Test saving config to JSON file."""
        config = PipelineConfig(
            name="test",
            platform="macos",
            architecture="arm64",
            modules=[BuildModuleConfig(name="clean")],
        )

        output_file = tmp_path / "output.json"
        config.to_file(output_file, format="json")

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["name"] == "test"


class TestBuildEnvironmentConfig:
    """Tests for BuildEnvironmentConfig."""

    def test_create_environment_config(self):
        """Test creating environment configuration."""
        config = BuildEnvironmentConfig(
            chromium_version="137.0.7151.69",
            browseros_version="0.36.3",
        )

        assert config.chromium_version == "137.0.7151.69"
        assert config.browseros_version == "0.36.3"
        assert config.build_offset == 5  # Default

    def test_invalid_version_format_rejected(self):
        """Test that invalid version format is rejected."""
        with pytest.raises(ValidationError, match="Invalid version format"):
            BuildEnvironmentConfig(
                chromium_version="137.0",  # Only 2 parts
                browseros_version="0.36.3",
            )

        with pytest.raises(ValidationError, match="Invalid version format"):
            BuildEnvironmentConfig(
                chromium_version="137.0.abc.69",  # Non-numeric
                browseros_version="0.36.3",
            )

    def test_optional_fields(self):
        """Test optional configuration fields."""
        config = BuildEnvironmentConfig(
            chromium_version="137.0.7151.69",
            browseros_version="0.36.3",
            enable_debug_symbols=False,
            enable_proprietary_codecs=True,
            signing_identity="Developer ID Application",
            notarization_team_id="TEAM123",
        )

        assert config.enable_debug_symbols is False
        assert config.enable_proprietary_codecs is True
        assert config.signing_identity == "Developer ID Application"


class TestConfigurationIntegration:
    """Integration tests for configuration system."""

    def test_complete_pipeline_configuration(self, reset_registry):
        """Test creating and validating a complete pipeline config."""

        @build_module(name="clean")
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(name="compile")
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        config = PipelineConfig(
            name="release_build",
            description="Full release build pipeline",
            platform="macos",
            architecture="universal",
            build_type="release",
            modules=[
                BuildModuleConfig(name="clean"),
                BuildModuleConfig(
                    name="compile",
                    parameters={"threads": 16, "verbose": True},
                ),
            ],
            environment={"CCACHE_DIR": "/tmp/ccache"},
        )

        # Validate modules exist
        config.validate_modules_exist()

        # Get enabled modules
        modules = config.get_enabled_modules()
        assert modules == ["clean", "compile"]

        # Verify configuration
        assert config.build_type == "release"
        assert config.environment["CCACHE_DIR"] == "/tmp/ccache"

    def test_save_and_load_config(self, tmp_path, reset_registry):
        """Test saving and loading configuration."""

        @build_module(name="test")
        class TestModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        original = PipelineConfig(
            name="test",
            platform="linux",
            architecture="x64",
            build_type="debug",
            modules=[BuildModuleConfig(name="test", parameters={"key": "value"})],
        )

        # Save to file
        config_file = tmp_path / "config.json"
        original.to_file(config_file, format="json")

        # Load from file
        loaded = PipelineConfig.from_file(config_file)

        # Verify same configuration
        assert loaded.name == original.name
        assert loaded.platform == original.platform
        assert loaded.modules[0].name == original.modules[0].name
        assert loaded.modules[0].parameters == original.modules[0].parameters
