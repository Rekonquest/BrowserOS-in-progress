"""Test fixtures for build modules."""

from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock, patch

import pytest

from build.common.module import CommandModule
from build.common.registry import ModuleRegistry, build_module


@pytest.fixture
def mock_module():
    """
    Create a mock build module for testing.

    Returns:
        Factory function that creates mock modules

    Example:
        def test_pipeline(mock_module):
            module = mock_module(name="test", phase="build")
            module.execute(context)
            assert module.execute.called
    """

    def _create_module(
        name: str = "test_module",
        phase: str = "build",
        requires: list[str] | None = None,
        produces: list[str] | None = None,
        execute_fn: Callable | None = None,
        validate_fn: Callable | None = None,
    ) -> CommandModule:
        """
        Create a mock module with specified configuration.

        Args:
            name: Module name
            phase: Build phase
            requires: List of required artifacts
            produces: List of produced artifacts
            execute_fn: Custom execute function
            validate_fn: Custom validate function

        Returns:
            Mock module instance
        """
        requires = requires or []
        produces = produces or []

        @build_module(
            name=name,
            phase=phase,
            requires=requires,
            produces=produces,
            description=f"Test module {name}",
        )
        class TestModule(CommandModule):
            def validate(self, context: Any) -> None:
                if validate_fn:
                    validate_fn(context)

            def execute(self, context: Any) -> None:
                if execute_fn:
                    execute_fn(context)

        return TestModule()

    return _create_module


@pytest.fixture
def mock_commands():
    """
    Mock subprocess commands for testing.

    Returns:
        Context manager that patches subprocess.run

    Example:
        def test_compile(mock_commands, mock_context):
            with mock_commands(return_code=0, stdout="Success"):
                module = CompileModule()
                module.execute(mock_context)
    """

    class MockCommands:
        def __init__(self):
            self.calls = []
            self._patch = None
            self._mock_run = None

        def __call__(
            self,
            return_code: int = 0,
            stdout: str = "",
            stderr: str = "",
            side_effect: Exception | None = None,
        ):
            """
            Configure mock command behavior.

            Args:
                return_code: Return code for commands
                stdout: Standard output
                stderr: Standard error
                side_effect: Exception to raise

            Returns:
                Self for use as context manager
            """
            self.return_code = return_code
            self.stdout = stdout
            self.stderr = stderr
            self.side_effect = side_effect
            return self

        def __enter__(self):
            """Enter context manager."""

            def mock_run(cmd, *args, **kwargs):
                """Mock subprocess.run."""
                self.calls.append(
                    {"cmd": cmd, "args": args, "kwargs": kwargs}
                )

                if self.side_effect:
                    raise self.side_effect

                result = MagicMock()
                result.returncode = self.return_code
                result.stdout = self.stdout
                result.stderr = self.stderr
                return result

            self._patch = patch("subprocess.run", side_effect=mock_run)
            self._mock_run = self._patch.__enter__()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Exit context manager."""
            if self._patch:
                self._patch.__exit__(exc_type, exc_val, exc_tb)

        def assert_called_with(self, *expected_cmds: str):
            """
            Assert that specific commands were called.

            Args:
                expected_cmds: Expected command strings
            """
            actual_cmds = [call["cmd"] for call in self.calls]
            for expected in expected_cmds:
                assert (
                    expected in str(actual_cmds)
                ), f"Expected command '{expected}' not found in {actual_cmds}"

        def assert_not_called(self):
            """Assert that no commands were called."""
            assert len(self.calls) == 0, f"Expected no calls, but got {self.calls}"

    return MockCommands()


@pytest.fixture
def mock_file_operations(tmp_path: Path):
    """
    Mock file operations for testing.

    Returns:
        Helper for creating and verifying test files

    Example:
        def test_output(mock_file_operations):
            output_file = mock_file_operations.create_file("output.txt", "content")
            # ... test code ...
            mock_file_operations.assert_file_contains(output_file, "expected")
    """

    class FileOperations:
        def __init__(self, base_path: Path):
            self.base_path = base_path

        def create_file(self, relative_path: str, content: str = "") -> Path:
            """
            Create a file with content.

            Args:
                relative_path: Path relative to base_path
                content: File content

            Returns:
                Path to created file
            """
            file_path = self.base_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return file_path

        def assert_file_exists(self, path: Path):
            """Assert that file exists."""
            assert path.exists(), f"File {path} does not exist"

        def assert_file_not_exists(self, path: Path):
            """Assert that file does not exist."""
            assert not path.exists(), f"File {path} exists but shouldn't"

        def assert_file_contains(self, path: Path, expected: str):
            """Assert that file contains expected string."""
            self.assert_file_exists(path)
            content = path.read_text()
            assert (
                expected in content
            ), f"Expected '{expected}' in file {path}, but got: {content}"

        def assert_file_equals(self, path: Path, expected: str):
            """Assert that file content equals expected."""
            self.assert_file_exists(path)
            content = path.read_text()
            assert (
                content == expected
            ), f"Expected file content '{expected}', but got: {content}"

    return FileOperations(tmp_path)


@pytest.fixture(autouse=True)
def reset_registry():
    """
    Reset module registry before each test.

    This ensures tests don't interfere with each other's
    module registrations.
    """
    ModuleRegistry.reset()
    yield
    ModuleRegistry.reset()


__all__ = [
    "mock_module",
    "mock_commands",
    "mock_file_operations",
    "reset_registry",
]
