#!/usr/bin/env python3
"""
Logging utilities for the build system
Provides consistent logging with Typer output and file logging

Modern logger with context manager support and sensitive data sanitization.
"""

from __future__ import annotations

import re
import typer
from pathlib import Path
from datetime import datetime
from typing import Optional, TextIO
from types import TracebackType

# Sensitive environment variable patterns that should be sanitized in logs
SENSITIVE_PATTERNS = [
    "MACOS_NOTARIZATION_PWD",
    "ESIGNER_PASSWORD",
    "CODE_SIGN_CERTIFICATE",
    "WINDOWS_CERTIFICATE_PASSWORD",
    "AWS_SECRET_ACCESS_KEY",
    "GITHUB_TOKEN",
    "API_KEY",
    "SECRET",
    "PASSWORD",
    "TOKEN",
]


class BuildLogger:
    """
    Modern logger with context manager support.

    Usage:
        # As context manager (recommended)
        with BuildLogger() as logger:
            logger.info("Building...")
            logger.success("Done!")

        # Or using global instance for backward compatibility
        logger = BuildLogger.get_instance()
        logger.info("Building...")
    """

    _instance: Optional[BuildLogger] = None

    def __init__(self, log_dir: Optional[Path] = None, sanitize: bool = True):
        """
        Initialize the logger.

        Args:
            log_dir: Directory for log files (default: package_root/logs)
            sanitize: Whether to sanitize sensitive data in logs
        """
        self._log_file: Optional[TextIO] = None
        self._log_dir = log_dir
        self._sanitize = sanitize
        self._log_file_path: Optional[Path] = None

    def __enter__(self) -> BuildLogger:
        """Enter context manager - opens log file."""
        self._ensure_log_file()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit context manager - closes log file."""
        self.close()

    def _ensure_log_file(self) -> TextIO:
        """Ensure log file is created with timestamp."""
        if self._log_file is None:
            if self._log_dir is None:
                from .paths import get_package_root

                self._log_dir = get_package_root() / "logs"

            # Create logs directory if it doesn't exist
            self._log_dir.mkdir(exist_ok=True)

            # Create log file with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self._log_file_path = self._log_dir / f"build_{timestamp}.log"

            # Open with UTF-8 encoding to handle any characters
            self._log_file = open(self._log_file_path, "w", encoding="utf-8")
            self._log_file.write(
                f"BrowserOS Build Log - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            self._log_file.write("=" * 80 + "\n\n")

        return self._log_file

    def _sanitize_message(self, message: str) -> str:
        """
        Sanitize sensitive data from log messages.

        Args:
            message: Original message

        Returns:
            Sanitized message with sensitive data replaced
        """
        if not self._sanitize:
            return message

        sanitized = message

        # Replace sensitive values in env var assignments (KEY=value)
        for pattern in SENSITIVE_PATTERNS:
            # Match: PATTERN=anything or PATTERN='anything' or PATTERN="anything"
            regex = rf"({pattern}\s*=\s*)(['\"]?)([^'\"\s]+)(['\"]?)"
            sanitized = re.sub(regex, r"\1\2***REDACTED***\4", sanitized, flags=re.IGNORECASE)

        return sanitized

    def _log_to_file(self, message: str) -> None:
        """Write message to log file with timestamp."""
        log_file = self._ensure_log_file()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sanitized = self._sanitize_message(message)
        log_file.write(f"[{timestamp}] {sanitized}\n")
        log_file.flush()

    def info(self, message: str) -> None:
        """Print info message using Typer."""
        typer.echo(message)
        self._log_to_file(f"INFO: {message}")

    def warning(self, message: str) -> None:
        """Print warning message with color."""
        typer.secho(f"⚠️  {message}", fg=typer.colors.YELLOW)
        self._log_to_file(f"WARNING: {message}")

    def error(self, message: str) -> None:
        """Print error message to stderr with color."""
        typer.secho(f"❌ {message}", fg=typer.colors.RED, err=True)
        self._log_to_file(f"ERROR: {message}")

    def success(self, message: str) -> None:
        """Print success message with color."""
        typer.secho(f"✅ {message}", fg=typer.colors.GREEN)
        self._log_to_file(f"SUCCESS: {message}")

    def debug(self, message: str, enabled: bool = False) -> None:
        """Print debug message if enabled."""
        if enabled:
            typer.secho(f"🔍 {message}", fg=typer.colors.BLUE, dim=True)
            self._log_to_file(f"DEBUG: {message}")

    def close(self) -> None:
        """Close the log file if it's open."""
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    @property
    def log_file_path(self) -> Optional[Path]:
        """Get the path to the current log file."""
        return self._log_file_path

    @classmethod
    def get_instance(cls) -> BuildLogger:
        """
        Get singleton instance for backward compatibility.

        Returns:
            Global BuildLogger instance
        """
        if cls._instance is None:
            cls._instance = BuildLogger()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (mainly for testing)."""
        if cls._instance:
            cls._instance.close()
            cls._instance = None


# =============================================================================
# Backward-compatible global functions
# =============================================================================

# Global logger instance (lazy initialization)
_global_logger: Optional[BuildLogger] = None


def _get_global_logger() -> BuildLogger:
    """Get or create global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = BuildLogger.get_instance()
    return _global_logger


def _log_to_file(message: str) -> None:
    """Write message to log file with timestamp (backward compatible)."""
    logger = _get_global_logger()
    logger._log_to_file(message)


def log_info(message: str) -> None:
    """Print info message using Typer."""
    logger = _get_global_logger()
    logger.info(message)


def log_warning(message: str) -> None:
    """Print warning message with color."""
    logger = _get_global_logger()
    logger.warning(message)


def log_error(message: str) -> None:
    """Print error message to stderr with color."""
    logger = _get_global_logger()
    logger.error(message)


def log_success(message: str) -> None:
    """Print success message with color."""
    logger = _get_global_logger()
    logger.success(message)


def log_debug(message: str, enabled: bool = False) -> None:
    """Print debug message if enabled."""
    logger = _get_global_logger()
    logger.debug(message, enabled)


def close_log_file() -> None:
    """Close the log file if it's open."""
    logger = _get_global_logger()
    logger.close()


# Export all logging functions
__all__ = [
    "BuildLogger",
    "log_info",
    "log_warning",
    "log_error",
    "log_success",
    "log_debug",
    "close_log_file",
    "_log_to_file",  # Internal use by utils.run_command
]