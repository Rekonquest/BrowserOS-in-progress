# Build System Modernization Plan

**Goal:** Transform the build system into a modern, testable, extensible architecture while maintaining 100% backward compatibility.

**Current Issues:** 38 identified issues across 10 categories
**Timeline:** 4 phases (incremental, can be deployed separately)

---

## Phase 1: Core Architecture Fixes (CRITICAL) 🔴

**Priority:** Highest - Blocks all other improvements
**Estimated Impact:** Enables testing, modularity, extensibility

### 1.1 Plugin-Based Module Discovery System

**Problem:** All modules hardcoded in `build/cli/build.py:58-86`

**Solution:** Dynamic module discovery with decorators

```python
# New pattern
@build_module(
    name="compile",
    phase="build",
    requires=["configured"],
    produces=["built_app"]
)
class CompileModule(CommandModule):
    ...
```

**Benefits:**
- Add modules without editing core files
- Modules self-register on import
- Can load external plugins from other packages

**Files to Create:**
- `build/common/registry.py` - Module registry with decorator
- `build/common/discovery.py` - Auto-discovery from modules/

**Files to Modify:**
- `build/cli/build.py` - Use registry instead of AVAILABLE_MODULES
- All module files - Add @build_module decorator

---

### 1.2 Split Context God Object

**Problem:** 617-line Context class does everything

**Solution:** Decompose into focused components

```python
# New structure
@dataclass
class BuildContext:
    """Orchestrates build components."""
    paths: PathManager
    versions: VersionManager
    artifacts: ArtifactManager
    platform: PlatformInfo
    config: BuildConfig
```

**Components:**
1. **VersionManager** - Centralized version handling
   - Load from files with validation
   - Calculate derived versions
   - Provide version properties

2. **PathManager** - All path operations
   - Resolve paths based on platform
   - Validate path existence
   - Construct artifact paths

3. **ArtifactManager** - Unified artifact tracking
   - Replace dual system (dict + registry)
   - Type-safe artifact registration
   - Dependency tracking

4. **BuildConfig** - Immutable build configuration
   - Architecture, build_type, etc.
   - Validation on construction
   - No runtime modification

**Benefits:**
- Each class has single responsibility
- Can test components independently
- Clear data flow between components
- Easier to understand and maintain

**Files to Create:**
- `build/common/version.py` - VersionManager
- `build/common/artifacts.py` - ArtifactManager (migrate from context.py)
- `build/common/paths.py` - PathManager (migrate from context.py)

**Files to Modify:**
- `build/common/context.py` - Thin orchestration layer
- All modules - Update to use context.paths, context.versions, etc.

---

### 1.3 Module Dependency Validation

**Problem:** `requires` and `produces` declared but ignored

**Solution:** Dependency graph validation before execution

```python
# Validate dependencies
validator = DependencyValidator(modules)
validator.validate()  # Raises if circular deps or missing requirements

# Auto-order modules
executor = PipelineExecutor(modules)
execution_order = executor.topological_sort()
```

**Benefits:**
- Catch dependency errors before pipeline starts
- Automatic ordering based on dependencies
- Clear error messages about what's missing

**Files to Create:**
- `build/common/dependencies.py` - Dependency graph validation
- `build/common/executor.py` - Pipeline executor with validation

**Files to Modify:**
- `build/cli/build.py` - Use executor instead of EXECUTION_ORDER
- All modules - Ensure requires/produces are accurate

---

## Phase 2: Error Handling & Observability 🟠

**Priority:** High - Improves debugging and reliability

### 2.1 Rich Error Context

**Problem:** Generic errors, lost context

**Solution:** Structured error types with context preservation

```python
class BuildError(Exception):
    """Base build error with context."""
    def __init__(self, message: str, context: dict[str, Any]):
        self.message = message
        self.context = context
        super().__init__(self._format_error())

    def _format_error(self) -> str:
        ctx_str = "\n".join(f"  {k}: {v}" for k, v in self.context.items())
        return f"{self.message}\nContext:\n{ctx_str}"

# Usage
raise BuildError(
    "Failed to compile",
    context={
        "architecture": "arm64",
        "build_type": "release",
        "command": cmd,
        "exit_code": result.returncode,
        "log_file": log_path,
    }
)
```

**Benefits:**
- Users get actionable error messages
- Context preserved for debugging
- Can filter/aggregate errors

**Files to Create:**
- `build/common/exceptions.py` - Structured exception hierarchy

**Files to Modify:**
- All modules - Use specific exceptions
- `build/common/utils.py` - Wrap subprocess errors

---

### 2.2 Progress Reporting & Observability

**Problem:** No visibility into what's happening

**Solution:** Progress hooks and structured logging

```python
class ProgressReporter:
    def on_module_start(self, module: str, phase: str): ...
    def on_module_complete(self, module: str, duration: float): ...
    def on_artifact_created(self, artifact: str, path: Path): ...

# Integration
with ProgressReporter() as progress:
    for module in pipeline:
        progress.on_module_start(module.name, module.phase)
        module.execute(ctx)
        progress.on_module_complete(module.name, elapsed)
```

**Benefits:**
- Users see progress in real-time
- Can add multiple reporters (console, file, webhook)
- Metrics for build performance

**Files to Create:**
- `build/common/progress.py` - Progress reporter interface

---

## Phase 3: Testing Infrastructure 🟡

**Priority:** Medium - Enables safe refactoring

### 3.1 Module Testing Framework

**Problem:** No tests, can't mock dependencies

**Solution:** Test fixtures and dependency injection

```python
# Fixture factory
@pytest.fixture
def build_context(tmp_path):
    """Create test context with temp directories."""
    return BuildContext(
        root_dir=tmp_path,
        chromium_src=tmp_path / "chromium",
        # ... auto-creates mock structure
    )

# Module test
def test_compile_module(build_context, mock_ninja):
    module = CompileModule()
    module.execute(build_context)
    assert build_context.artifacts.has("built_app")
```

**Files to Create:**
- `tests/fixtures/context.py` - BuildContext fixtures
- `tests/fixtures/modules.py` - Module test helpers
- `tests/modules/test_*.py` - Module tests

---

### 3.2 Integration Tests

**Problem:** No way to test full pipeline without real build

**Solution:** Mock external commands, test pipeline flow

```python
def test_full_pipeline(build_context, mock_commands):
    """Test complete build pipeline."""
    pipeline = ["clean", "configure", "compile", "sign", "package"]
    executor = PipelineExecutor(pipeline, build_context)

    executor.execute()

    # Verify all artifacts created
    assert build_context.artifacts.has("signed_app")
    assert build_context.artifacts.has("installer")
```

**Files to Create:**
- `tests/integration/test_pipeline.py`
- `tests/mocks/commands.py` - Mock subprocess calls

---

## Phase 4: Extensibility & Developer Experience 🟢

**Priority:** Low - Nice to have enhancements

### 4.1 Module Hooks

**Solution:** Pre/post execution hooks

```python
@build_module("compile")
class CompileModule(CommandModule):
    def pre_execute(self, ctx: BuildContext) -> None:
        """Called before execute()."""
        pass

    def post_execute(self, ctx: BuildContext) -> None:
        """Called after execute() succeeds."""
        pass

    def on_failure(self, ctx: BuildContext, error: Exception) -> None:
        """Called if execute() raises."""
        pass
```

---

### 4.2 Configuration Schema Validation

**Solution:** Pydantic models for YAML configs

```python
class BuildModuleConfig(BaseModel):
    name: str
    enabled: bool = True
    parameters: dict[str, Any] = {}

class PipelineConfig(BaseModel):
    modules: list[BuildModuleConfig]
    platform: Literal["windows", "macos", "linux"]
    architecture: Literal["x64", "arm64", "universal"]

    @validator("modules")
    def validate_modules_exist(cls, modules):
        # Check all modules are registered
        ...
```

**Files to Create:**
- `build/common/config_schema.py` - Pydantic models

---

### 4.3 Improved CLI

**Solution:** Better help, autocomplete, interactive mode

```python
# Module suggestions
$ browseros build --modules <TAB>
clean  configure  compile  sign  package

# Interactive module selection
$ browseros build --interactive
? Select modules to run:
  ◉ clean
  ◉ configure
  ◉ compile
  ◯ sign (requires code signing credentials)
  ◯ package
```

---

## Implementation Order

### Week 1: Core Architecture
1. ✅ Module discovery system
2. ✅ Dependency validation
3. ✅ Basic tests for new components

### Week 2: Context Refactoring
1. ✅ VersionManager extraction
2. ✅ PathManager extraction
3. ✅ ArtifactManager migration
4. ✅ Update all modules

### Week 3: Error Handling
1. ✅ Structured exceptions
2. ✅ Progress reporting
3. ✅ Better error messages

### Week 4: Testing & Polish
1. ✅ Module test framework
2. ✅ Integration tests
3. ✅ Documentation

---

## Success Metrics

- ✅ All 38 issues addressed
- ✅ 80%+ test coverage
- ✅ Add module without editing core files
- ✅ 100% backward compatible
- ✅ Faster developer onboarding

---

## Migration Strategy

**Backward Compatibility:**
- Old APIs remain functional
- New APIs are opt-in
- Deprecation warnings guide migration
- Both systems run in parallel during transition

**Example:**
```python
# Old way (still works)
ctx.artifacts["built_app"] = [path]

# New way (recommended)
ctx.artifacts.add("built_app", path)
```

---

## Quick Wins (Can Do Immediately)

1. ✅ Add @build_module decorator (3 hours)
2. ✅ Extract VersionManager (4 hours)
3. ✅ Add dependency validator (5 hours)
4. ✅ Create test fixtures (3 hours)

Total: ~15 hours for massive improvements

---

## Next Steps

1. Review this plan
2. Approve Phase 1 approach
3. Start with module discovery system
4. Iterate with feedback
