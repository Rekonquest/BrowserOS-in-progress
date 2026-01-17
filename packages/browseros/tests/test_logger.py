"""Tests for build.common.logger module."""

import re
from pathlib import Path

import pytest

from build.common.logger import BuildLogger


class TestBuildLogger:
    """Tests for BuildLogger class."""

    def test_logger_context_manager(self, temp_dir):
        """Test logger as context manager."""
        with BuildLogger(log_dir=temp_dir) as logger:
            assert logger._log_file is not None
            assert logger.log_file_path is not None
            assert logger.log_file_path.exists()

        # File should be closed after context
        assert logger._log_file is None

    def test_logger_creates_log_file(self, temp_dir):
        """Test logger creates log file with timestamp."""
        logger = BuildLogger(log_dir=temp_dir)
        logger._ensure_log_file()

        assert logger.log_file_path is not None
        assert logger.log_file_path.exists()
        assert logger.log_file_path.parent == temp_dir
        assert logger.log_file_path.name.startswith("build_")
        assert logger.log_file_path.name.endswith(".log")

        logger.close()

    def test_logger_info(self, temp_dir, capsys):
        """Test info logging."""
        with BuildLogger(log_dir=temp_dir) as logger:
            logger.info("Test info message")

        captured = capsys.readouterr()
        assert "Test info message" in captured.out

        # Check log file
        log_content = logger.log_file_path.read_text()
        assert "INFO: Test info message" in log_content

    def test_logger_sanitizes_passwords(self, temp_dir):
        """Test sensitive data sanitization."""
        with BuildLogger(log_dir=temp_dir, sanitize=True) as logger:
            logger.info("Setting PASSWORD=secret123")
            logger.info("Using API_KEY='my-secret-key'")
            logger.info("Token: TOKEN=abc123")

        log_content = logger.log_file_path.read_text()

        # Passwords should be sanitized in log file
        assert "secret123" not in log_content
        assert "my-secret-key" not in log_content
        assert "abc123" not in log_content
        assert "***REDACTED***" in log_content

    def test_logger_no_sanitization_when_disabled(self, temp_dir):
        """Test that sanitization can be disabled."""
        with BuildLogger(log_dir=temp_dir, sanitize=False) as logger:
            logger.info("PASSWORD=secret123")

        log_content = logger.log_file_path.read_text()

        # Password should NOT be sanitized when disabled
        assert "secret123" in log_content

    def test_logger_sanitizes_common_secrets(self, temp_dir):
        """Test sanitization of common secret patterns."""
        with BuildLogger(log_dir=temp_dir, sanitize=True) as logger:
            logger.info("GITHUB_TOKEN=ghp_1234567890")
            logger.info("AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI")
            logger.info("MACOS_NOTARIZATION_PWD=apple_password")

        log_content = logger.log_file_path.read_text()

        assert "ghp_1234567890" not in log_content
        assert "wJalrXUtnFEMI" not in log_content
        assert "apple_password" not in log_content

    def test_logger_multiple_messages(self, temp_dir):
        """Test logging multiple messages."""
        with BuildLogger(log_dir=temp_dir) as logger:
            logger.info("Message 1")
            logger.warning("Message 2")
            logger.error("Message 3")
            logger.success("Message 4")

        log_content = logger.log_file_path.read_text()

        assert "INFO: Message 1" in log_content
        assert "WARNING: Message 2" in log_content
        assert "ERROR: Message 3" in log_content
        assert "SUCCESS: Message 4" in log_content

    def test_logger_close(self, temp_dir):
        """Test explicit close."""
        logger = BuildLogger(log_dir=temp_dir)
        logger._ensure_log_file()

        assert logger._log_file is not None

        logger.close()

        assert logger._log_file is None

    def test_logger_singleton(self):
        """Test singleton pattern."""
        logger1 = BuildLogger.get_instance()
        logger2 = BuildLogger.get_instance()

        assert logger1 is logger2

        # Clean up
        BuildLogger.reset_instance()

    def test_logger_reset_instance(self):
        """Test resetting singleton instance."""
        logger1 = BuildLogger.get_instance()
        BuildLogger.reset_instance()
        logger2 = BuildLogger.get_instance()

        assert logger1 is not logger2


class TestBackwardCompatibleFunctions:
    """Tests for backward-compatible global functions."""

    def test_log_info_function(self, capsys):
        """Test global log_info function."""
        from build.common.logger import log_info, close_log_file

        log_info("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.out

        close_log_file()

    def test_close_log_file_function(self):
        """Test global close_log_file function."""
        from build.common.logger import (
            BuildLogger,
            close_log_file,
            log_info,
        )

        # Reset to clean state
        BuildLogger.reset_instance()

        log_info("Test")
        close_log_file()

        # Clean up
        BuildLogger.reset_instance()
