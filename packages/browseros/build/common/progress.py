#!/usr/bin/env python3
"""
Progress reporting and observability for the build system.

This module provides a flexible progress reporting system with multiple
reporter backends (console, file, webhooks, etc.).

Example:
    with ProgressReporter() as progress:
        progress.on_module_start("compile", "build")
        # ... do work ...
        progress.on_module_complete("compile", duration=45.2)
        progress.on_artifact_created("built_app", Path("/path/to/app"))
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table


@dataclass
class ModuleEvent:
    """Event for module lifecycle."""

    module: str
    phase: str
    event_type: str  # "start", "complete", "error"
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[float] = None
    error: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtifactEvent:
    """Event for artifact creation."""

    artifact: str
    path: Path
    size: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProgressReporterProtocol(Protocol):
    """Protocol for progress reporters."""

    def on_module_start(self, module: str, phase: str) -> None:
        """Called when module starts executing."""
        ...

    def on_module_complete(self, module: str, duration: float) -> None:
        """Called when module completes successfully."""
        ...

    def on_module_error(self, module: str, error: Exception) -> None:
        """Called when module fails."""
        ...

    def on_artifact_created(
        self, artifact: str, path: Path, size: Optional[int] = None
    ) -> None:
        """Called when artifact is created."""
        ...

    def on_pipeline_start(self, modules: list[str]) -> None:
        """Called when pipeline starts."""
        ...

    def on_pipeline_complete(self, duration: float) -> None:
        """Called when pipeline completes."""
        ...


class BaseProgressReporter(ABC):
    """Base class for progress reporters."""

    def __init__(self):
        """Initialize reporter."""
        self._start_time: Optional[float] = None
        self._module_start_times: dict[str, float] = {}
        self._events: list[ModuleEvent | ArtifactEvent] = []

    def __enter__(self) -> BaseProgressReporter:
        """Enter context manager."""
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type is None and self._start_time is not None:
            duration = time.time() - self._start_time
            self.on_pipeline_complete(duration)

    @abstractmethod
    def on_module_start(self, module: str, phase: str) -> None:
        """Called when module starts executing."""
        pass

    @abstractmethod
    def on_module_complete(self, module: str, duration: float) -> None:
        """Called when module completes successfully."""
        pass

    @abstractmethod
    def on_module_error(self, module: str, error: Exception) -> None:
        """Called when module fails."""
        pass

    @abstractmethod
    def on_artifact_created(
        self, artifact: str, path: Path, size: Optional[int] = None
    ) -> None:
        """Called when artifact is created."""
        pass

    @abstractmethod
    def on_pipeline_start(self, modules: list[str]) -> None:
        """Called when pipeline starts."""
        pass

    @abstractmethod
    def on_pipeline_complete(self, duration: float) -> None:
        """Called when pipeline completes."""
        pass


class ConsoleProgressReporter(BaseProgressReporter):
    """Console-based progress reporter using Rich."""

    def __init__(self, verbose: bool = False):
        """
        Initialize console reporter.

        Args:
            verbose: Show detailed progress information
        """
        super().__init__()
        self.verbose = verbose
        self.console = Console()
        self._progress: Optional[Progress] = None
        self._task_id: Optional[TaskID] = None
        self._total_modules = 0
        self._completed_modules = 0

    def __enter__(self) -> ConsoleProgressReporter:
        """Enter context manager."""
        super().__enter__()
        if self.verbose:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
            )
            self._progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._progress:
            self._progress.__exit__(exc_type, exc_val, exc_tb)
        super().__exit__(exc_type, exc_val, exc_tb)

    def on_pipeline_start(self, modules: list[str]) -> None:
        """Called when pipeline starts."""
        self._total_modules = len(modules)
        self._completed_modules = 0

        if self.verbose:
            self.console.print(
                f"\n[bold blue]Starting build pipeline[/bold blue] "
                f"with {self._total_modules} modules"
            )
            table = Table(show_header=False, box=None)
            for i, module in enumerate(modules, 1):
                table.add_row(f"  {i}. {module}")
            self.console.print(table)
            self.console.print()

        if self._progress:
            self._task_id = self._progress.add_task(
                "Building...", total=self._total_modules
            )

    def on_module_start(self, module: str, phase: str) -> None:
        """Called when module starts executing."""
        self._module_start_times[module] = time.time()

        event = ModuleEvent(
            module=module, phase=phase, event_type="start", context={}
        )
        self._events.append(event)

        if self.verbose:
            self.console.print(
                f"[cyan]▶[/cyan] Starting [bold]{module}[/bold] ({phase})"
            )
        elif not self._progress:
            self.console.print(f"[cyan]▶[/cyan] {module}")

        if self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id, description=f"Building {module}..."
            )

    def on_module_complete(self, module: str, duration: float) -> None:
        """Called when module completes successfully."""
        self._completed_modules += 1

        event = ModuleEvent(
            module=module,
            phase="",
            event_type="complete",
            duration=duration,
        )
        self._events.append(event)

        if self.verbose:
            self.console.print(
                f"[green]✓[/green] Completed [bold]{module}[/bold] "
                f"in {duration:.1f}s"
            )

        if self._progress and self._task_id is not None:
            self._progress.update(self._task_id, advance=1)

    def on_module_error(self, module: str, error: Exception) -> None:
        """Called when module fails."""
        event = ModuleEvent(
            module=module,
            phase="",
            event_type="error",
            error=str(error),
        )
        self._events.append(event)

        self.console.print(
            f"[red]✗[/red] Failed [bold]{module}[/bold]: {error}"
        )

    def on_artifact_created(
        self, artifact: str, path: Path, size: Optional[int] = None
    ) -> None:
        """Called when artifact is created."""
        event = ArtifactEvent(
            artifact=artifact,
            path=path,
            size=size,
        )
        self._events.append(event)

        if self.verbose:
            size_str = f" ({self._format_size(size)})" if size else ""
            self.console.print(
                f"  [dim]→ Created artifact:[/dim] {artifact}{size_str}"
            )

    def on_pipeline_complete(self, duration: float) -> None:
        """Called when pipeline completes."""
        if self.verbose:
            self.console.print()
            self.console.print(
                f"[bold green]✓ Pipeline completed[/bold green] "
                f"in {duration:.1f}s"
            )
            self.console.print(
                f"  Modules: {self._completed_modules}/{self._total_modules}"
            )
        else:
            self.console.print(
                f"\n[green]✓[/green] Build completed in {duration:.1f}s"
            )

    @staticmethod
    def _format_size(size: Optional[int]) -> str:
        """Format file size in human-readable format."""
        if size is None:
            return ""

        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class FileProgressReporter(BaseProgressReporter):
    """File-based progress reporter (JSON lines format)."""

    def __init__(self, output_file: Path):
        """
        Initialize file reporter.

        Args:
            output_file: Path to output file (will be created/overwritten)
        """
        super().__init__()
        self.output_file = output_file
        self._file = None

    def __enter__(self) -> FileProgressReporter:
        """Enter context manager."""
        super().__enter__()
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.output_file, "w")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        # Call parent first to write pipeline_complete event
        super().__exit__(exc_type, exc_val, exc_tb)
        # Then close the file
        if self._file:
            self._file.close()

    def _write_event(self, event: dict[str, Any]) -> None:
        """Write event to file as JSON line."""
        if self._file:
            self._file.write(json.dumps(event) + "\n")
            self._file.flush()

    def on_pipeline_start(self, modules: list[str]) -> None:
        """Called when pipeline starts."""
        self._write_event(
            {
                "type": "pipeline_start",
                "timestamp": datetime.now().isoformat(),
                "modules": modules,
                "total": len(modules),
            }
        )

    def on_module_start(self, module: str, phase: str) -> None:
        """Called when module starts executing."""
        self._module_start_times[module] = time.time()
        self._write_event(
            {
                "type": "module_start",
                "timestamp": datetime.now().isoformat(),
                "module": module,
                "phase": phase,
            }
        )

    def on_module_complete(self, module: str, duration: float) -> None:
        """Called when module completes successfully."""
        self._write_event(
            {
                "type": "module_complete",
                "timestamp": datetime.now().isoformat(),
                "module": module,
                "duration": duration,
            }
        )

    def on_module_error(self, module: str, error: Exception) -> None:
        """Called when module fails."""
        self._write_event(
            {
                "type": "module_error",
                "timestamp": datetime.now().isoformat(),
                "module": module,
                "error": str(error),
                "error_type": type(error).__name__,
            }
        )

    def on_artifact_created(
        self, artifact: str, path: Path, size: Optional[int] = None
    ) -> None:
        """Called when artifact is created."""
        self._write_event(
            {
                "type": "artifact_created",
                "timestamp": datetime.now().isoformat(),
                "artifact": artifact,
                "path": str(path),
                "size": size,
            }
        )

    def on_pipeline_complete(self, duration: float) -> None:
        """Called when pipeline completes."""
        self._write_event(
            {
                "type": "pipeline_complete",
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
            }
        )


class CompositeProgressReporter(BaseProgressReporter):
    """Composite reporter that forwards to multiple reporters."""

    def __init__(self, reporters: list[BaseProgressReporter]):
        """
        Initialize composite reporter.

        Args:
            reporters: List of reporters to forward to
        """
        super().__init__()
        self.reporters = reporters

    def __enter__(self) -> CompositeProgressReporter:
        """Enter context manager."""
        super().__enter__()
        for reporter in self.reporters:
            reporter.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        # Call parent first to send pipeline_complete to all reporters
        super().__exit__(exc_type, exc_val, exc_tb)
        # Then close all reporters' resources (files, etc) without triggering their __exit__
        for reporter in self.reporters:
            # Close files directly for FileProgressReporter
            if hasattr(reporter, '_file') and reporter._file:
                reporter._file.close()
            # Close progress display for ConsoleProgressReporter
            if hasattr(reporter, '_progress') and reporter._progress:
                reporter._progress.__exit__(exc_type, exc_val, exc_tb)

    def on_pipeline_start(self, modules: list[str]) -> None:
        """Called when pipeline starts."""
        for reporter in self.reporters:
            reporter.on_pipeline_start(modules)

    def on_module_start(self, module: str, phase: str) -> None:
        """Called when module starts executing."""
        for reporter in self.reporters:
            reporter.on_module_start(module, phase)

    def on_module_complete(self, module: str, duration: float) -> None:
        """Called when module completes successfully."""
        for reporter in self.reporters:
            reporter.on_module_complete(module, duration)

    def on_module_error(self, module: str, error: Exception) -> None:
        """Called when module fails."""
        for reporter in self.reporters:
            reporter.on_module_error(module, error)

    def on_artifact_created(
        self, artifact: str, path: Path, size: Optional[int] = None
    ) -> None:
        """Called when artifact is created."""
        for reporter in self.reporters:
            reporter.on_artifact_created(artifact, path, size)

    def on_pipeline_complete(self, duration: float) -> None:
        """Called when pipeline completes."""
        for reporter in self.reporters:
            reporter.on_pipeline_complete(duration)


class NullProgressReporter(BaseProgressReporter):
    """No-op reporter for when progress reporting is disabled."""

    def on_pipeline_start(self, modules: list[str]) -> None:
        """No-op."""
        pass

    def on_module_start(self, module: str, phase: str) -> None:
        """No-op."""
        pass

    def on_module_complete(self, module: str, duration: float) -> None:
        """No-op."""
        pass

    def on_module_error(self, module: str, error: Exception) -> None:
        """No-op."""
        pass

    def on_artifact_created(
        self, artifact: str, path: Path, size: Optional[int] = None
    ) -> None:
        """No-op."""
        pass

    def on_pipeline_complete(self, duration: float) -> None:
        """No-op."""
        pass


# Convenience function
def create_progress_reporter(
    verbose: bool = False,
    output_file: Optional[Path] = None,
) -> BaseProgressReporter:
    """
    Create a progress reporter with common configuration.

    Args:
        verbose: Show detailed progress information
        output_file: Optional file to write events to

    Returns:
        Configured progress reporter

    Example:
        reporter = create_progress_reporter(verbose=True, output_file=Path("build.log"))
        with reporter as progress:
            progress.on_module_start("compile", "build")
    """
    reporters = [ConsoleProgressReporter(verbose=verbose)]

    if output_file:
        reporters.append(FileProgressReporter(output_file))

    if len(reporters) == 1:
        return reporters[0]
    return CompositeProgressReporter(reporters)


__all__ = [
    "ModuleEvent",
    "ArtifactEvent",
    "ProgressReporterProtocol",
    "BaseProgressReporter",
    "ConsoleProgressReporter",
    "FileProgressReporter",
    "CompositeProgressReporter",
    "NullProgressReporter",
    "create_progress_reporter",
]
