"""Tests for build.common.progress module."""

import json
import time
from pathlib import Path

import pytest

from build.common.progress import (
    ArtifactEvent,
    CompositeProgressReporter,
    ConsoleProgressReporter,
    FileProgressReporter,
    ModuleEvent,
    NullProgressReporter,
    create_progress_reporter,
)


class TestModuleEvent:
    """Tests for ModuleEvent dataclass."""

    def test_create_module_event(self):
        """Test creating a module event."""
        event = ModuleEvent(
            module="compile",
            phase="build",
            event_type="start",
        )

        assert event.module == "compile"
        assert event.phase == "build"
        assert event.event_type == "start"
        assert event.timestamp is not None
        assert event.duration is None
        assert event.error is None

    def test_module_event_with_duration(self):
        """Test module event with duration."""
        event = ModuleEvent(
            module="compile",
            phase="build",
            event_type="complete",
            duration=45.2,
        )

        assert event.duration == 45.2

    def test_module_event_with_error(self):
        """Test module event with error."""
        event = ModuleEvent(
            module="compile",
            phase="build",
            event_type="error",
            error="Compilation failed",
        )

        assert event.error == "Compilation failed"


class TestArtifactEvent:
    """Tests for ArtifactEvent dataclass."""

    def test_create_artifact_event(self):
        """Test creating an artifact event."""
        path = Path("/path/to/artifact")
        event = ArtifactEvent(
            artifact="built_app",
            path=path,
        )

        assert event.artifact == "built_app"
        assert event.path == path
        assert event.timestamp is not None
        assert event.size is None

    def test_artifact_event_with_size(self):
        """Test artifact event with size."""
        event = ArtifactEvent(
            artifact="built_app",
            path=Path("/path/to/artifact"),
            size=1024000,
        )

        assert event.size == 1024000


class TestConsoleProgressReporter:
    """Tests for ConsoleProgressReporter."""

    def test_context_manager(self):
        """Test using reporter as context manager."""
        reporter = ConsoleProgressReporter()

        with reporter as progress:
            assert progress._start_time is not None

        # Should call on_pipeline_complete
        assert reporter._start_time is not None

    def test_pipeline_start(self):
        """Test pipeline start event."""
        reporter = ConsoleProgressReporter(verbose=True)

        with reporter:
            reporter.on_pipeline_start(["clean", "configure", "compile"])

            assert reporter._total_modules == 3
            assert reporter._completed_modules == 0

    def test_module_lifecycle(self):
        """Test complete module lifecycle."""
        reporter = ConsoleProgressReporter()

        with reporter:
            reporter.on_pipeline_start(["compile"])

            # Start module
            reporter.on_module_start("compile", "build")
            assert "compile" in reporter._module_start_times
            assert len(reporter._events) == 1

            # Complete module
            time.sleep(0.1)
            reporter.on_module_complete("compile", duration=0.1)
            assert reporter._completed_modules == 1
            assert len(reporter._events) == 2

    def test_module_error(self):
        """Test module error handling."""
        reporter = ConsoleProgressReporter()

        with reporter:
            reporter.on_pipeline_start(["compile"])
            reporter.on_module_start("compile", "build")

            error = Exception("Build failed")
            reporter.on_module_error("compile", error)

            # Should record error event
            error_events = [
                e for e in reporter._events if isinstance(e, ModuleEvent) and e.event_type == "error"
            ]
            assert len(error_events) == 1
            assert error_events[0].error == "Build failed"

    def test_artifact_created(self):
        """Test artifact creation event."""
        reporter = ConsoleProgressReporter(verbose=True)

        with reporter:
            path = Path("/path/to/app")
            reporter.on_artifact_created("built_app", path, size=1024000)

            artifact_events = [
                e for e in reporter._events if isinstance(e, ArtifactEvent)
            ]
            assert len(artifact_events) == 1
            assert artifact_events[0].artifact == "built_app"
            assert artifact_events[0].path == path
            assert artifact_events[0].size == 1024000

    def test_format_size(self):
        """Test file size formatting."""
        reporter = ConsoleProgressReporter()

        assert reporter._format_size(500) == "500.0 B"
        assert reporter._format_size(1024) == "1.0 KB"
        assert reporter._format_size(1024 * 1024) == "1.0 MB"
        assert reporter._format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert reporter._format_size(None) == ""


class TestFileProgressReporter:
    """Tests for FileProgressReporter."""

    def test_create_reporter(self, tmp_path):
        """Test creating file reporter."""
        output_file = tmp_path / "progress.jsonl"
        reporter = FileProgressReporter(output_file)

        assert reporter.output_file == output_file

    def test_write_events_to_file(self, tmp_path):
        """Test writing events to file."""
        output_file = tmp_path / "progress.jsonl"
        reporter = FileProgressReporter(output_file)

        with reporter:
            reporter.on_pipeline_start(["clean", "compile"])
            reporter.on_module_start("clean", "setup")
            reporter.on_module_complete("clean", duration=1.5)

        # Read events from file
        assert output_file.exists()
        events = []
        with open(output_file) as f:
            for line in f:
                events.append(json.loads(line))

        assert len(events) == 4  # pipeline_start + module_start + module_complete + pipeline_complete
        assert events[0]["type"] == "pipeline_start"
        assert events[0]["modules"] == ["clean", "compile"]
        assert events[1]["type"] == "module_start"
        assert events[1]["module"] == "clean"
        assert events[2]["type"] == "module_complete"
        assert events[2]["duration"] == 1.5

    def test_module_error_event(self, tmp_path):
        """Test writing module error event."""
        output_file = tmp_path / "progress.jsonl"
        reporter = FileProgressReporter(output_file)

        with reporter:
            reporter.on_module_start("compile", "build")
            reporter.on_module_error("compile", ValueError("Invalid argument"))

        events = []
        with open(output_file) as f:
            for line in f:
                events.append(json.loads(line))

        error_event = events[1]
        assert error_event["type"] == "module_error"
        assert error_event["module"] == "compile"
        assert error_event["error"] == "Invalid argument"
        assert error_event["error_type"] == "ValueError"

    def test_artifact_created_event(self, tmp_path):
        """Test writing artifact created event."""
        output_file = tmp_path / "progress.jsonl"
        reporter = FileProgressReporter(output_file)

        with reporter:
            reporter.on_artifact_created(
                "built_app", Path("/path/to/app"), size=5000000
            )

        events = []
        with open(output_file) as f:
            for line in f:
                events.append(json.loads(line))

        artifact_event = events[0]
        assert artifact_event["type"] == "artifact_created"
        assert artifact_event["artifact"] == "built_app"
        assert artifact_event["path"] == "/path/to/app"
        assert artifact_event["size"] == 5000000

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        output_file = tmp_path / "subdir" / "nested" / "progress.jsonl"
        reporter = FileProgressReporter(output_file)

        with reporter:
            reporter.on_module_start("test", "test")

        assert output_file.exists()
        assert output_file.parent.exists()


class TestCompositeProgressReporter:
    """Tests for CompositeProgressReporter."""

    def test_forwards_to_multiple_reporters(self, tmp_path):
        """Test that events are forwarded to all reporters."""
        output_file = tmp_path / "progress.jsonl"

        console_reporter = ConsoleProgressReporter()
        file_reporter = FileProgressReporter(output_file)
        composite = CompositeProgressReporter([console_reporter, file_reporter])

        with composite:
            composite.on_pipeline_start(["clean", "compile"])
            composite.on_module_start("clean", "setup")
            composite.on_module_complete("clean", duration=1.5)

        # Check console reporter received events
        assert len(console_reporter._events) == 2

        # Check file reporter wrote events
        assert output_file.exists()
        events = []
        with open(output_file) as f:
            for line in f:
                events.append(json.loads(line))
        assert len(events) == 4

    def test_context_manager_with_multiple_reporters(self, tmp_path):
        """Test context manager handles all reporters."""
        file1 = tmp_path / "progress1.jsonl"
        file2 = tmp_path / "progress2.jsonl"

        reporter1 = FileProgressReporter(file1)
        reporter2 = FileProgressReporter(file2)
        composite = CompositeProgressReporter([reporter1, reporter2])

        with composite:
            composite.on_module_start("test", "test")

        # Both files should exist
        assert file1.exists()
        assert file2.exists()


class TestNullProgressReporter:
    """Tests for NullProgressReporter."""

    def test_null_reporter_does_nothing(self):
        """Test that null reporter doesn't do anything."""
        reporter = NullProgressReporter()

        # Should not raise any errors
        with reporter:
            reporter.on_pipeline_start(["clean", "compile"])
            reporter.on_module_start("clean", "setup")
            reporter.on_module_complete("clean", duration=1.5)
            reporter.on_module_error("compile", Exception("error"))
            reporter.on_artifact_created("artifact", Path("/path"))

        # No events should be recorded
        assert len(reporter._events) == 0


class TestCreateProgressReporter:
    """Tests for create_progress_reporter factory function."""

    def test_create_console_reporter(self):
        """Test creating console reporter."""
        reporter = create_progress_reporter(verbose=True)

        assert isinstance(reporter, ConsoleProgressReporter)
        assert reporter.verbose is True

    def test_create_composite_reporter(self, tmp_path):
        """Test creating composite reporter with file output."""
        output_file = tmp_path / "progress.jsonl"
        reporter = create_progress_reporter(verbose=False, output_file=output_file)

        assert isinstance(reporter, CompositeProgressReporter)
        assert len(reporter.reporters) == 2
        assert isinstance(reporter.reporters[0], ConsoleProgressReporter)
        assert isinstance(reporter.reporters[1], FileProgressReporter)

    def test_create_simple_console_reporter(self):
        """Test creating simple console reporter without file."""
        reporter = create_progress_reporter(verbose=False, output_file=None)

        assert isinstance(reporter, ConsoleProgressReporter)
        assert not isinstance(reporter, CompositeProgressReporter)


class TestProgressReporterIntegration:
    """Integration tests for progress reporting."""

    def test_full_pipeline_reporting(self, tmp_path):
        """Test reporting a complete pipeline execution."""
        output_file = tmp_path / "progress.jsonl"
        reporter = create_progress_reporter(verbose=True, output_file=output_file)

        modules = ["clean", "configure", "compile", "sign", "package"]

        with reporter:
            reporter.on_pipeline_start(modules)

            for module in modules:
                reporter.on_module_start(module, "build")
                time.sleep(0.01)  # Simulate work
                reporter.on_module_complete(module, duration=0.01)

                # Create artifacts for some modules
                if module == "compile":
                    reporter.on_artifact_created(
                        "built_app", Path("/out/BrowserOS.app"), size=500000000
                    )
                elif module == "package":
                    reporter.on_artifact_created(
                        "installer", Path("/out/BrowserOS.dmg"), size=600000000
                    )

        # Verify file output
        events = []
        with open(output_file) as f:
            for line in f:
                events.append(json.loads(line))

        # Should have: pipeline_start + 5*(module_start + module_complete) + 2*artifact_created + pipeline_complete
        assert len(events) == 1 + 5 * 2 + 2 + 1

        # Verify structure
        assert events[0]["type"] == "pipeline_start"
        assert events[-1]["type"] == "pipeline_complete"
        assert events[-1]["duration"] > 0

    def test_pipeline_with_errors(self, tmp_path):
        """Test reporting pipeline with module errors."""
        output_file = tmp_path / "progress.jsonl"
        reporter = FileProgressReporter(output_file)

        with reporter:
            reporter.on_pipeline_start(["clean", "compile"])
            reporter.on_module_start("clean", "setup")
            reporter.on_module_complete("clean", duration=1.0)
            reporter.on_module_start("compile", "build")
            reporter.on_module_error("compile", Exception("Compilation failed"))

        events = []
        with open(output_file) as f:
            for line in f:
                events.append(json.loads(line))

        # Find error event
        error_events = [e for e in events if e["type"] == "module_error"]
        assert len(error_events) == 1
        assert error_events[0]["module"] == "compile"
        assert "Compilation failed" in error_events[0]["error"]
