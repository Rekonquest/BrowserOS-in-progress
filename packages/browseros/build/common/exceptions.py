#!/usr/bin/env python3
"""
Structured exception hierarchy for the build system.

This module provides a comprehensive exception hierarchy for better error
handling, reporting, and debugging.

Example:
    try:
        build_module.execute(context)
    except ModuleExecutionError as e:
        log_error(f"Module failed: {e}")
        log_debug(f"Full context: {e.context}")
        if e.suggestion:
            log_info(f"Suggestion: {e.suggestion}")
"""

from __future__ import annotations

from typing import Any, Optional


class BuildError(Exception):
    """
    Base exception for all build system errors.

    All build system exceptions should inherit from this class for
    consistent error handling and reporting.

    Attributes:
        message: Human-readable error message
        context: Additional context information (module, file, line, etc.)
        suggestion: Optional suggestion for fixing the error
        original_error: Original exception if this wraps another error
    """

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize build error.

        Args:
            message: Human-readable error message
            context: Additional context (module, file, command, etc.)
            suggestion: Optional suggestion for fixing the error
            original_error: Original exception if wrapping another error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.suggestion = suggestion
        self.original_error = original_error

    def __str__(self) -> str:
        """Get formatted error string."""
        parts = [self.message]

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        if self.original_error:
            parts.append(f"Caused by: {self.original_error}")

        return "\n".join(parts)


# Configuration and Validation Errors


class ConfigurationError(BuildError):
    """Raised when build configuration is invalid or missing."""

    pass


class ValidationError(BuildError):
    """Raised when validation fails (pre-execution checks)."""

    pass


class EnvironmentError(BuildError):
    """Raised when required environment variables or conditions are missing."""

    pass


# Execution Errors


class ExecutionError(BuildError):
    """Base class for errors during module execution."""

    pass


class ModuleExecutionError(ExecutionError):
    """Raised when a build module fails during execution."""

    pass


class CommandExecutionError(ExecutionError):
    """Raised when an external command fails."""

    def __init__(
        self,
        message: str,
        command: str,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        """
        Initialize command execution error.

        Args:
            message: Error message
            command: The command that failed
            exit_code: Exit code from the command
            stdout: Standard output from the command
            stderr: Standard error from the command
            context: Additional context
            suggestion: Suggestion for fixing the error
        """
        ctx = context or {}
        ctx.update(
            {
                "command": command,
                "exit_code": exit_code,
                "stdout": stdout[:500] if stdout else None,  # Truncate
                "stderr": stderr[:500] if stderr else None,  # Truncate
            }
        )
        super().__init__(message, context=ctx, suggestion=suggestion)
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class TimeoutError(ExecutionError):
    """Raised when an operation times out."""

    pass


# File and Path Errors


class FileError(BuildError):
    """Base class for file-related errors."""

    pass


class FileNotFoundError(FileError):
    """Raised when a required file is not found."""

    pass


class FilePermissionError(FileError):
    """Raised when file permissions are insufficient."""

    pass


class FileCorruptedError(FileError):
    """Raised when a file is corrupted or invalid."""

    pass


# Resource Errors


class ResourceError(BuildError):
    """Base class for resource-related errors."""

    pass


class DiskSpaceError(ResourceError):
    """Raised when insufficient disk space is available."""

    pass


class MemoryError(ResourceError):
    """Raised when insufficient memory is available."""

    pass


class NetworkError(ResourceError):
    """Raised when network operations fail."""

    pass


# Module and Plugin Errors


class ModuleError(BuildError):
    """Base class for module-related errors."""

    pass


class ModuleNotFoundError(ModuleError):
    """Raised when a module cannot be found."""

    pass


class ModuleRegistrationError(ModuleError):
    """Raised when module registration fails."""

    pass


class PluginError(BuildError):
    """Raised when plugin loading or execution fails."""

    pass


# Signature and Security Errors


class SignatureError(BuildError):
    """Base class for signature-related errors."""

    pass


class SignatureVerificationError(SignatureError):
    """Raised when signature verification fails."""

    pass


class SignatureCreationError(SignatureError):
    """Raised when signature creation fails."""

    pass


class CertificateError(BuildError):
    """Raised when certificate validation fails."""

    pass


# Platform Errors


class PlatformError(BuildError):
    """Raised when platform-specific operations fail."""

    pass


class UnsupportedPlatformError(PlatformError):
    """Raised when operation is not supported on current platform."""

    pass


# Version Errors


class VersionError(BuildError):
    """Base class for version-related errors."""

    pass


class VersionMismatchError(VersionError):
    """Raised when version requirements are not met."""

    pass


class VersionParseError(VersionError):
    """Raised when version string cannot be parsed."""

    pass


# Artifact Errors


class ArtifactError(BuildError):
    """Base class for artifact-related errors."""

    pass


class ArtifactNotFoundError(ArtifactError):
    """Raised when required artifact is not found."""

    pass


class ArtifactCorruptedError(ArtifactError):
    """Raised when artifact is corrupted or invalid."""

    pass


class ArtifactSignatureError(ArtifactError):
    """Raised when artifact signature is invalid."""

    pass


# OTA Update Errors


class OTAError(BuildError):
    """Base class for OTA update errors."""

    pass


class OTAPackageError(OTAError):
    """Raised when OTA package creation fails."""

    pass


class OTAUploadError(OTAError):
    """Raised when OTA package upload fails."""

    pass


# Helper Functions


def wrap_error(
    original_error: Exception,
    message: str,
    error_class: type[BuildError] = BuildError,
    context: Optional[dict[str, Any]] = None,
    suggestion: Optional[str] = None,
) -> BuildError:
    """
    Wrap an existing exception in a BuildError.

    This is useful for converting third-party exceptions into our
    structured exception hierarchy while preserving the original error.

    Args:
        original_error: The original exception
        message: New error message to show
        error_class: BuildError subclass to use (default: BuildError)
        context: Additional context information
        suggestion: Optional suggestion for fixing the error

    Returns:
        BuildError instance wrapping the original error

    Example:
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise wrap_error(
                e,
                "Failed to compile Chromium",
                CommandExecutionError,
                context={"module": "compile"},
                suggestion="Check that all dependencies are installed"
            )
    """
    return error_class(
        message=message,
        context=context,
        suggestion=suggestion,
        original_error=original_error,
    )


def create_error_with_suggestion(
    error_class: type[BuildError],
    message: str,
    suggestion: str,
    context: Optional[dict[str, Any]] = None,
) -> BuildError:
    """
    Create a BuildError with a helpful suggestion.

    Args:
        error_class: BuildError subclass to create
        message: Error message
        suggestion: Helpful suggestion for fixing the error
        context: Additional context

    Returns:
        BuildError instance with suggestion

    Example:
        raise create_error_with_suggestion(
            FileNotFoundError,
            "CHROMIUM_VERSION file not found",
            "Run 'browseros setup init' to initialize the build directory",
            context={"file": "CHROMIUM_VERSION"}
        )
    """
    return error_class(message=message, context=context, suggestion=suggestion)


__all__ = [
    # Base
    "BuildError",
    # Configuration
    "ConfigurationError",
    "ValidationError",
    "EnvironmentError",
    # Execution
    "ExecutionError",
    "ModuleExecutionError",
    "CommandExecutionError",
    "TimeoutError",
    # Files
    "FileError",
    "FileNotFoundError",
    "FilePermissionError",
    "FileCorruptedError",
    # Resources
    "ResourceError",
    "DiskSpaceError",
    "MemoryError",
    "NetworkError",
    # Modules
    "ModuleError",
    "ModuleNotFoundError",
    "ModuleRegistrationError",
    "PluginError",
    # Signatures
    "SignatureError",
    "SignatureVerificationError",
    "SignatureCreationError",
    "CertificateError",
    # Platform
    "PlatformError",
    "UnsupportedPlatformError",
    # Versions
    "VersionError",
    "VersionMismatchError",
    "VersionParseError",
    # Artifacts
    "ArtifactError",
    "ArtifactNotFoundError",
    "ArtifactCorruptedError",
    "ArtifactSignatureError",
    # OTA
    "OTAError",
    "OTAPackageError",
    "OTAUploadError",
    # Helpers
    "wrap_error",
    "create_error_with_suggestion",
]
