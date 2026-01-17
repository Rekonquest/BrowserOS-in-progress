"""Tests for build.common.exceptions module."""

import pytest

from build.common.exceptions import (
    ArtifactNotFoundError,
    BuildError,
    CertificateError,
    CommandExecutionError,
    ConfigurationError,
    DiskSpaceError,
    EnvironmentError,
    ExecutionError,
    FileNotFoundError,
    FilePermissionError,
    ModuleExecutionError,
    ModuleNotFoundError,
    NetworkError,
    OTAPackageError,
    PlatformError,
    PluginError,
    SignatureVerificationError,
    TimeoutError,
    UnsupportedPlatformError,
    ValidationError,
    VersionMismatchError,
    create_error_with_suggestion,
    wrap_error,
)


class TestBuildError:
    """Tests for BuildError base class."""

    def test_basic_error(self):
        """Test creating a basic error."""
        error = BuildError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.context == {}
        assert error.suggestion is None
        assert error.original_error is None

    def test_error_with_context(self):
        """Test error with context information."""
        error = BuildError(
            "Build failed",
            context={"module": "compile", "file": "main.cc"},
        )

        assert "Build failed" in str(error)
        assert "module=compile" in str(error)
        assert "file=main.cc" in str(error)
        assert error.context["module"] == "compile"
        assert error.context["file"] == "main.cc"

    def test_error_with_suggestion(self):
        """Test error with helpful suggestion."""
        error = BuildError(
            "Configuration file not found",
            suggestion="Run 'browseros init' to create default configuration",
        )

        assert "Configuration file not found" in str(error)
        assert "Run 'browseros init'" in str(error)
        assert error.suggestion == "Run 'browseros init' to create default configuration"

    def test_error_with_original_error(self):
        """Test error wrapping another exception."""
        original = ValueError("Invalid value")
        error = BuildError(
            "Failed to parse config",
            original_error=original,
        )

        assert "Failed to parse config" in str(error)
        assert "Invalid value" in str(error)
        assert error.original_error is original

    def test_error_with_all_fields(self):
        """Test error with all fields populated."""
        original = OSError("File not found")
        error = BuildError(
            "Build initialization failed",
            context={"step": "init", "phase": "setup"},
            suggestion="Check that all required files exist",
            original_error=original,
        )

        error_str = str(error)
        assert "Build initialization failed" in error_str
        assert "step=init" in error_str
        assert "phase=setup" in error_str
        assert "Check that all required files exist" in error_str
        assert "File not found" in error_str


class TestConfigurationErrors:
    """Tests for configuration-related errors."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid build type")
        assert isinstance(error, BuildError)
        assert "Invalid build type" in str(error)

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError(
            "Module validation failed",
            context={"module": "compile"},
        )
        assert isinstance(error, BuildError)
        assert "Module validation failed" in str(error)

    def test_environment_error(self):
        """Test EnvironmentError."""
        error = EnvironmentError(
            "CHROMIUM_SRC not set",
            suggestion="Set CHROMIUM_SRC environment variable",
        )
        assert isinstance(error, BuildError)
        assert "CHROMIUM_SRC not set" in str(error)


class TestExecutionErrors:
    """Tests for execution-related errors."""

    def test_execution_error(self):
        """Test ExecutionError base class."""
        error = ExecutionError("Execution failed")
        assert isinstance(error, BuildError)

    def test_module_execution_error(self):
        """Test ModuleExecutionError."""
        error = ModuleExecutionError(
            "Compile module failed",
            context={"module": "compile", "step": "ninja"},
        )
        assert isinstance(error, ExecutionError)
        assert isinstance(error, BuildError)

    def test_command_execution_error(self):
        """Test CommandExecutionError."""
        error = CommandExecutionError(
            message="Command failed",
            command="ninja -C out/Default",
            exit_code=1,
            stdout="Building...",
            stderr="Error: compilation failed",
        )

        assert isinstance(error, ExecutionError)
        assert error.command == "ninja -C out/Default"
        assert error.exit_code == 1
        assert "ninja -C out/Default" in str(error)
        assert "exit_code=1" in str(error)

    def test_command_execution_error_truncates_output(self):
        """Test that long output is truncated."""
        long_output = "x" * 1000
        error = CommandExecutionError(
            message="Command failed",
            command="test",
            stdout=long_output,
            stderr=long_output,
        )

        # Output should be truncated to 500 chars
        assert error.context["stdout"] == "x" * 500
        assert error.context["stderr"] == "x" * 500

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError(
            "Operation timed out after 300s",
            context={"timeout": 300, "operation": "compile"},
        )
        assert isinstance(error, ExecutionError)


class TestFileErrors:
    """Tests for file-related errors."""

    def test_file_not_found_error(self):
        """Test FileNotFoundError."""
        error = FileNotFoundError(
            "CHROMIUM_VERSION not found",
            context={"file": "/path/to/CHROMIUM_VERSION"},
        )
        assert isinstance(error, BuildError)

    def test_file_permission_error(self):
        """Test FilePermissionError."""
        error = FilePermissionError(
            "Cannot write to output directory",
            suggestion="Check directory permissions",
        )
        assert isinstance(error, BuildError)


class TestResourceErrors:
    """Tests for resource-related errors."""

    def test_disk_space_error(self):
        """Test DiskSpaceError."""
        error = DiskSpaceError(
            "Insufficient disk space",
            context={"required": "50GB", "available": "10GB"},
        )
        assert isinstance(error, BuildError)
        assert "required=50GB" in str(error)

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError(
            "Failed to download artifact",
            context={"url": "https://example.com/file"},
        )
        assert isinstance(error, BuildError)


class TestModuleErrors:
    """Tests for module-related errors."""

    def test_module_not_found_error(self):
        """Test ModuleNotFoundError."""
        error = ModuleNotFoundError(
            "Module 'custom_build' not found",
            suggestion="Check module name or run 'browseros build --list'",
        )
        assert isinstance(error, BuildError)

    def test_plugin_error(self):
        """Test PluginError."""
        error = PluginError(
            "Failed to load plugin",
            context={"plugin": "my_plugin.py"},
        )
        assert isinstance(error, BuildError)


class TestSignatureErrors:
    """Tests for signature-related errors."""

    def test_signature_verification_error(self):
        """Test SignatureVerificationError."""
        error = SignatureVerificationError(
            "Invalid signature",
            context={"file": "BrowserOS.app"},
        )
        assert isinstance(error, BuildError)

    def test_certificate_error(self):
        """Test CertificateError."""
        error = CertificateError(
            "Certificate expired",
            context={"certificate": "Developer ID"},
        )
        assert isinstance(error, BuildError)


class TestPlatformErrors:
    """Tests for platform-related errors."""

    def test_platform_error(self):
        """Test PlatformError."""
        error = PlatformError("Platform-specific operation failed")
        assert isinstance(error, BuildError)

    def test_unsupported_platform_error(self):
        """Test UnsupportedPlatformError."""
        error = UnsupportedPlatformError(
            "This module only runs on macOS",
            context={"current_platform": "linux", "required_platform": "macos"},
        )
        assert isinstance(error, PlatformError)


class TestVersionErrors:
    """Tests for version-related errors."""

    def test_version_mismatch_error(self):
        """Test VersionMismatchError."""
        error = VersionMismatchError(
            "Version mismatch",
            context={"expected": "137.0.7151.69", "actual": "136.0.7100.50"},
        )
        assert isinstance(error, BuildError)


class TestArtifactErrors:
    """Tests for artifact-related errors."""

    def test_artifact_not_found_error(self):
        """Test ArtifactNotFoundError."""
        error = ArtifactNotFoundError(
            "Artifact 'built_app' not found",
            suggestion="Run 'browseros build compile' first",
        )
        assert isinstance(error, BuildError)


class TestOTAErrors:
    """Tests for OTA-related errors."""

    def test_ota_package_error(self):
        """Test OTAPackageError."""
        error = OTAPackageError(
            "Failed to create OTA package",
            context={"version": "0.36.3"},
        )
        assert isinstance(error, BuildError)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_wrap_error(self):
        """Test wrap_error function."""
        original = ValueError("Invalid configuration")
        wrapped = wrap_error(
            original,
            "Failed to load config",
            ConfigurationError,
            context={"file": "config.yaml"},
            suggestion="Check YAML syntax",
        )

        assert isinstance(wrapped, ConfigurationError)
        assert wrapped.message == "Failed to load config"
        assert wrapped.original_error is original
        assert wrapped.context["file"] == "config.yaml"
        assert wrapped.suggestion == "Check YAML syntax"
        assert "Invalid configuration" in str(wrapped)

    def test_wrap_error_default_class(self):
        """Test wrap_error with default error class."""
        original = Exception("Something went wrong")
        wrapped = wrap_error(original, "Operation failed")

        assert isinstance(wrapped, BuildError)
        assert wrapped.original_error is original

    def test_create_error_with_suggestion(self):
        """Test create_error_with_suggestion function."""
        error = create_error_with_suggestion(
            FileNotFoundError,
            "Build directory not found",
            "Run 'browseros init' to create build directory",
            context={"directory": "/path/to/build"},
        )

        assert isinstance(error, FileNotFoundError)
        assert error.message == "Build directory not found"
        assert error.suggestion == "Run 'browseros init' to create build directory"
        assert error.context["directory"] == "/path/to/build"
        assert "Run 'browseros init'" in str(error)


class TestErrorInheritance:
    """Tests for error inheritance hierarchy."""

    def test_all_errors_inherit_from_build_error(self):
        """Test that all custom errors inherit from BuildError."""
        error_classes = [
            ConfigurationError,
            ValidationError,
            EnvironmentError,
            ExecutionError,
            ModuleExecutionError,
            TimeoutError,
            FileNotFoundError,
            FilePermissionError,
            DiskSpaceError,
            NetworkError,
            ModuleNotFoundError,
            PluginError,
            SignatureVerificationError,
            CertificateError,
            PlatformError,
            UnsupportedPlatformError,
            VersionMismatchError,
            ArtifactNotFoundError,
            OTAPackageError,
        ]

        for error_class in error_classes:
            error = error_class("test message")
            assert isinstance(error, BuildError)
            assert isinstance(error, Exception)

        # CommandExecutionError has special constructor
        cmd_error = CommandExecutionError("test message", command="test_cmd")
        assert isinstance(cmd_error, BuildError)
        assert isinstance(cmd_error, Exception)

    def test_catch_by_category(self):
        """Test that errors can be caught by category."""
        # Should catch ExecutionError and subclasses
        try:
            raise ModuleExecutionError("Module failed")
        except ExecutionError as e:
            assert isinstance(e, ModuleExecutionError)

        # Should catch BuildError and all subclasses
        try:
            raise UnsupportedPlatformError("Not supported")
        except BuildError as e:
            assert isinstance(e, UnsupportedPlatformError)
