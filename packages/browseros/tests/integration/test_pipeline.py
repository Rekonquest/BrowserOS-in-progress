"""Integration tests for build pipeline."""

import time
from pathlib import Path

import pytest

from build.common.dependencies import DependencyValidator
from build.common.progress import create_progress_reporter
from build.common.registry import build_module
from build.common.module import CommandModule


class TestPipelineIntegration:
    """Integration tests for complete build pipelines."""

    def test_simple_pipeline(self, mock_context, mock_commands):
        """Test a simple 3-module pipeline."""

        @build_module(name="clean", produces=["clean_workspace"])
        class CleanModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                # Simulate work
                context["artifacts"].add("clean_workspace", Path("/tmp/clean"))

        @build_module(
            name="configure",
            requires=["clean_workspace"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                # Verify prerequisite
                assert context["artifacts"].has("clean_workspace")
                context["artifacts"].add("configured", Path("/tmp/configured"))

        @build_module(
            name="compile",
            requires=["configured"],
            produces=["built_app"],
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                # Verify prerequisite
                assert context["artifacts"].has("configured")
                context["artifacts"].add("built_app", Path("/tmp/app"))

        # Validate dependencies
        validator = DependencyValidator(["clean", "configure", "compile"])
        validator.validate()

        # Get execution order
        execution_order = validator.execution_order()
        assert execution_order == ["clean", "configure", "compile"]

        # Execute pipeline
        modules = [CleanModule(), ConfigureModule(), CompileModule()]
        for module in modules:
            module.execute(mock_context)

        # Verify all artifacts created
        assert mock_context["artifacts"].has("clean_workspace")
        assert mock_context["artifacts"].has("configured")
        assert mock_context["artifacts"].has("built_app")

    def test_pipeline_with_parallel_modules(self, mock_context):
        """Test pipeline with independent parallel modules."""

        @build_module(name="module_a", produces=["artifact_a"])
        class ModuleA(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("artifact_a", Path("/tmp/a"))

        @build_module(name="module_b", produces=["artifact_b"])
        class ModuleB(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("artifact_b", Path("/tmp/b"))

        @build_module(
            name="module_c",
            requires=["artifact_a", "artifact_b"],
            produces=["artifact_c"],
        )
        class ModuleC(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                assert context["artifacts"].has("artifact_a")
                assert context["artifacts"].has("artifact_b")
                context["artifacts"].add("artifact_c", Path("/tmp/c"))

        # Validate dependencies
        validator = DependencyValidator(["module_a", "module_b", "module_c"])
        validator.validate()

        # Get execution order
        execution_order = validator.execution_order()

        # module_a and module_b can run in parallel, module_c must be last
        assert execution_order.index("module_c") == 2
        assert "module_a" in execution_order[:2]
        assert "module_b" in execution_order[:2]

        # Execute pipeline
        modules = {"module_a": ModuleA(), "module_b": ModuleB(), "module_c": ModuleC()}

        for module_name in execution_order:
            modules[module_name].execute(mock_context)

        # Verify all artifacts created
        assert mock_context["artifacts"].has("artifact_a")
        assert mock_context["artifacts"].has("artifact_b")
        assert mock_context["artifacts"].has("artifact_c")

    def test_pipeline_with_progress_reporting(self, mock_context, tmp_path):
        """Test pipeline with progress reporting."""
        output_file = tmp_path / "progress.jsonl"

        @build_module(name="step1", produces=["step1_done"])
        class Step1(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                time.sleep(0.01)
                context["artifacts"].add("step1_done", Path("/tmp/step1"))

        @build_module(
            name="step2",
            requires=["step1_done"],
            produces=["step2_done"],
        )
        class Step2(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                time.sleep(0.01)
                context["artifacts"].add("step2_done", Path("/tmp/step2"))

        # Create progress reporter
        reporter = create_progress_reporter(verbose=False, output_file=output_file)

        modules = [Step1(), Step2()]

        # Execute with progress reporting
        with reporter:
            reporter.on_pipeline_start(["step1", "step2"])

            for i, (module_name, module) in enumerate([("step1", modules[0]), ("step2", modules[1])]):
                reporter.on_module_start(module_name, "build")
                start_time = time.time()
                module.execute(mock_context)
                duration = time.time() - start_time
                reporter.on_module_complete(module_name, duration)

        # Verify progress file created
        assert output_file.exists()

        # Verify events recorded
        import json

        events = []
        with open(output_file) as f:
            for line in f:
                events.append(json.loads(line))

        assert len(events) > 0
        assert events[0]["type"] == "pipeline_start"
        assert events[-1]["type"] == "pipeline_complete"

    def test_pipeline_error_handling(self, mock_context):
        """Test pipeline handles module errors correctly."""

        @build_module(name="working_module", produces=["artifact1"])
        class WorkingModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("artifact1", Path("/tmp/artifact1"))

        @build_module(
            name="failing_module",
            requires=["artifact1"],
            produces=["artifact2"],
        )
        class FailingModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                raise RuntimeError("Module failed!")

        # Execute pipeline
        module1 = WorkingModule()
        module2 = FailingModule()

        # First module should succeed
        module1.execute(mock_context)
        assert mock_context["artifacts"].has("artifact1")

        # Second module should fail
        with pytest.raises(RuntimeError, match="Module failed"):
            module2.execute(mock_context)

        # artifact2 should not be created
        assert not mock_context["artifacts"].has("artifact2")

    def test_complex_dependency_graph(self, mock_context):
        """Test pipeline with complex multi-level dependencies."""

        @build_module(name="init", produces=["initialized"])
        class InitModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("initialized", Path("/tmp/init"))

        @build_module(
            name="fetch", requires=["initialized"], produces=["source_code"]
        )
        class FetchModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("source_code", Path("/tmp/source"))

        @build_module(
            name="patch", requires=["source_code"], produces=["patched_source"]
        )
        class PatchModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("patched_source", Path("/tmp/patched"))

        @build_module(
            name="configure",
            requires=["patched_source"],
            produces=["configured"],
        )
        class ConfigureModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("configured", Path("/tmp/configured"))

        @build_module(
            name="compile", requires=["configured"], produces=["built_app"]
        )
        class CompileModule(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                context["artifacts"].add("built_app", Path("/tmp/app"))

        # Validate dependencies
        modules_list = ["init", "fetch", "patch", "configure", "compile"]
        validator = DependencyValidator(modules_list)
        validator.validate()

        # Get execution order
        execution_order = validator.execution_order()

        # Verify correct order
        assert execution_order == modules_list

        # Execute pipeline
        modules = {
            "init": InitModule(),
            "fetch": FetchModule(),
            "patch": PatchModule(),
            "configure": ConfigureModule(),
            "compile": CompileModule(),
        }

        for module_name in execution_order:
            modules[module_name].execute(mock_context)

        # Verify all artifacts created
        for artifact in [
            "initialized",
            "source_code",
            "patched_source",
            "configured",
            "built_app",
        ]:
            assert mock_context["artifacts"].has(artifact)


class TestPipelineValidation:
    """Tests for pipeline validation."""

    def test_missing_dependency_detected(self):
        """Test that missing dependencies are detected."""

        @build_module(
            name="module_with_missing_dep",
            requires=["nonexistent"],
            produces=["output"],
        )
        class ModuleWithMissingDep(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        # Should raise MissingDependencyError
        from build.common.dependencies import MissingDependencyError

        with pytest.raises(MissingDependencyError):
            validator = DependencyValidator(["module_with_missing_dep"])
            validator.validate()

    def test_circular_dependency_detected(self):
        """Test that circular dependencies are detected."""

        @build_module(
            name="module_a",
            requires=["artifact_b"],
            produces=["artifact_a"],
        )
        class ModuleA(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        @build_module(
            name="module_b",
            requires=["artifact_a"],
            produces=["artifact_b"],
        )
        class ModuleB(CommandModule):
            def validate(self, context):
                pass

            def execute(self, context):
                pass

        # Should raise CircularDependencyError
        from build.common.dependencies import CircularDependencyError

        with pytest.raises(CircularDependencyError):
            validator = DependencyValidator(["module_a", "module_b"])
            validator.execution_order()
