# Build System Migration Guide

This guide shows how to migrate existing build modules to the new plugin-based system.

## Overview

**Old System:** Modules hardcoded in `build/cli/build.py`
**New System:** Modules self-register with `@build_module` decorator

**Benefits:**
- Add modules without editing core files
- Modules declare dependencies explicitly
- Can load external plugins
- Easier to test modules independently

---

## Migration Steps

### Step 1: Add @build_module Decorator

**Before:**
```python
# build/modules/compile.py
from ..common.module import CommandModule

class CompileModule(CommandModule):
    produces = ["built_app"]
    requires = ["configured"]
    description = "Compile Chromium sources"

    def validate(self, context):
        ...

    def execute(self, context):
        ...
```

**After:**
```python
# build/modules/compile.py
from ..common.module import CommandModule
from ..common.registry import build_module

@build_module(
    name="compile",           # Optional: auto-generated from class name
    phase="build",
    requires=["configured"],
    produces=["built_app"],
    description="Compile Chromium sources"
)
class CompileModule(CommandModule):
    def validate(self, context):
        ...

    def execute(self, context):
        ...
```

### Step 2: Remove Hardcoded Registration

**Before (in build/cli/build.py):**
```python
from ..modules.compile import CompileModule

AVAILABLE_MODULES = {
    "compile": CompileModule,
    # ... 29 more modules
}
```

**After (in build/cli/build.py):**
```python
from ..common.discovery import discover_modules

# Auto-discover all modules
registry = discover_modules()

# Use registry instead of AVAILABLE_MODULES
module_class = registry.get("compile")
```

### Step 3: Use Registry in CLI

**Before:**
```python
def build_command(modules: list[str]):
    for module_name in modules:
        if module_name not in AVAILABLE_MODULES:
            raise ValueError(f"Unknown module: {module_name}")

        module_class = AVAILABLE_MODULES[module_name]
        module = module_class()
        module.execute(context)
```

**After:**
```python
def build_command(modules: list[str]):
    registry = ModuleRegistry.get_instance()

    for module_name in modules:
        if not registry.has(module_name):
            raise ValueError(f"Unknown module: {module_name}")

        module_class = registry.get(module_name)
        module = module_class()
        module.execute(context)
```

---

## Platform-Specific Modules

### Marking Platform-Specific Modules

**macOS-only module:**
```python
@build_module(
    name="sign_macos",
    phase="sign",
    platform="macos",  # Only runs on macOS
    requires=["built_app"],
    produces=["signed_app"]
)
class MacOSSignModule(CommandModule):
    ...
```

**Getting modules for current platform:**
```python
from ..common.platform import Platform
from ..common.registry import ModuleRegistry

platform = Platform.current().name_lower
registry = ModuleRegistry.get_instance()

# Get all modules compatible with current platform
available = registry.get_by_platform(platform)
```

---

## Module Dependencies

### Declaring Dependencies

Dependencies are now validated automatically:

```python
@build_module(
    name="sign",
    requires=["built_app"],      # Needs these artifacts
    produces=["signed_app"],     # Creates these artifacts
)
class SignModule(CommandModule):
    def execute(self, context):
        # Get required artifact
        app_path = context.artifacts.get("built_app")

        # Sign the app
        signed_path = self.sign_app(app_path)

        # Register produced artifact
        context.artifacts.add("signed_app", signed_path)
```

### Dependency Validation

The system automatically validates dependencies:

```python
from ..common.dependencies import DependencyValidator

# Validate before execution
validator = DependencyValidator(["sign", "package"])
validator.validate()  # Raises if dependencies not met
```

---

## Example: Complete Migration

### Before (Old System)

**build/modules/package/macos.py:**
```python
from ...common.module import CommandModule
from ...common.utils import log_info

class MacOSPackageModule(CommandModule):
    produces = ["dmg"]
    requires = ["signed_app"]
    description = "Create macOS DMG installer"

    def validate(self, context):
        if not context.artifacts.has("signed_app"):
            raise ValidationError("Missing signed_app")

    def execute(self, context):
        log_info("Creating DMG...")
        # ... package logic ...
```

**build/cli/build.py:**
```python
from ..modules.package.macos import MacOSPackageModule

AVAILABLE_MODULES = {
    # ... other modules
    "package_macos": MacOSPackageModule,
}

def _get_package_module():
    if IS_MACOS():
        return "package_macos"
    elif IS_WINDOWS():
        return "package_windows"
    else:
        return "package_linux"
```

### After (New System)

**build/modules/package/macos.py:**
```python
from ...common.module import CommandModule
from ...common.registry import build_module
from ...common.utils import log_info

@build_module(
    name="package",        # Same name across platforms
    phase="package",
    platform="macos",      # Platform restriction
    requires=["signed_app"],
    produces=["dmg"],
    description="Create macOS DMG installer"
)
class MacOSPackageModule(CommandModule):
    def validate(self, context):
        # Dependency validation happens automatically
        pass

    def execute(self, context):
        log_info("Creating DMG...")
        # ... package logic ...
```

**build/cli/build.py:**
```python
from ..common.discovery import discover_modules
from ..common.platform import Platform

# Auto-discover all modules
discover_modules()

# Get platform-specific "package" module
registry = ModuleRegistry.get_instance()
platform = Platform.current().name_lower
package_module = registry.get_by_platform(platform)["package"]
```

---

## Testing Modules

### Old System (Hard to Test)

```python
# No easy way to test without full build environment
def test_compile():
    # Need to set up entire context
    context = BuildContext(...)  # Requires real files
    module = CompileModule()
    module.execute(context)
```

### New System (Easy to Test)

```python
# tests/modules/test_compile.py
import pytest
from build.common.registry import build_module
from build.modules.compile import CompileModule

def test_compile_module_registered():
    """Test that compile module is registered."""
    from build.common.discovery import validate_module_exists

    assert validate_module_exists("compile")

def test_compile_dependencies():
    """Test compile module declares dependencies."""
    from build.common.discovery import get_module_dependencies

    deps = get_module_dependencies("compile")

    assert "configured" in deps["requires"]
    assert "built_app" in deps["produces"]

def test_compile_execution(mock_build_context):
    """Test compile module execution."""
    module = CompileModule()
    module.execute(mock_build_context)

    assert mock_build_context.artifacts.has("built_app")
```

---

## External Plugins

### Creating External Plugins

External plugins can be loaded from any directory:

**~/.browseros/plugins/my_plugin.py:**
```python
from browseros.build.common.module import CommandModule
from browseros.build.common.registry import build_module

@build_module(
    name="my_custom_step",
    phase="build",
    description="My custom build step"
)
class MyPluginModule(CommandModule):
    def validate(self, context):
        pass

    def execute(self, context):
        print("Running my custom step!")
```

**Loading plugins:**
```python
from pathlib import Path
from build.common.discovery import discover_external_plugins

# Load plugins from home directory
plugin_count = discover_external_plugins([
    Path.home() / ".browseros/plugins"
])

print(f"Loaded {plugin_count} external plugins")
```

---

## Backward Compatibility

The new system maintains 100% backward compatibility:

1. **Old AVAILABLE_MODULES dict still works** (but deprecated)
2. **Modules without @build_module still work** (if manually registered)
3. **Both registration methods can coexist**

You can migrate modules incrementally - no need to convert everything at once.

---

## Checklist for Module Migration

- [ ] Add `@build_module` decorator to module class
- [ ] Specify `name`, `phase`, `requires`, `produces`
- [ ] Add `platform` restriction if module is platform-specific
- [ ] Remove hardcoded import from `build/cli/build.py`
- [ ] Remove entry from `AVAILABLE_MODULES` dict
- [ ] Test that module is discovered: `browseros build --list`
- [ ] Add unit tests for module
- [ ] Update module documentation

---

## Common Issues

### Module Not Discovered

**Problem:** Module not showing in `browseros build --list`

**Solutions:**
1. Ensure `@build_module` decorator is applied
2. Check that module file is in `build/modules/` directory
3. Verify module file is valid Python (no syntax errors)
4. Run with `--debug` to see discovery logs

### Duplicate Module Name

**Problem:** `ValueError: Module 'xyz' already registered`

**Solutions:**
1. Use unique module names
2. Use platform-specific names for platform modules
3. Override auto-generated name: `@build_module(name="unique_name")`

### Dependencies Not Validated

**Problem:** Module runs even when dependencies missing

**Solutions:**
1. Ensure `requires` list is accurate
2. Call `validator.validate()` before pipeline execution
3. Check that required modules actually `produce` what you need

---

## Questions?

If you encounter issues during migration, check:

1. **Module Registry:** `ModuleRegistry.get_instance().list_modules()`
2. **Module Metadata:** `registry.get_metadata("module_name")`
3. **Dependencies:** `get_module_dependencies("module_name")`

For more help, see:
- `BUILD_SYSTEM_MODERNIZATION.md` - Full modernization plan
- `tests/test_registry.py` - Example usage
- `tests/test_discovery.py` - Discovery examples
