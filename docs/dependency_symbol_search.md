# Dependency Symbol Search

Serena now includes advanced dependency symbol search capabilities that allow you to search for symbols not just in your project code, but also in external dependencies like NuGet packages and DLLs. This is particularly useful for projects that rely on external frameworks or libraries, such as game modding.

## Overview

The dependency symbol search feature extends Serena's existing symbol search capabilities to include:

- **NuGet Packages**: Search for types and members in referenced NuGet packages
- **External DLLs**: Search for symbols in external DLL dependencies from configured paths
- **System Assemblies**: Optionally include symbols from system assemblies
- **Decompilation Support**: Pluggable backends (ILSpy, Cecil) for symbol extraction

## Available Tools

### FindDependencySymbolTool

The main tool for searching dependency symbols:

```python
from serena.tools import FindDependencySymbolTool

# Search for NetPackageManager type in dependencies
result = agent.execute_task(
    lambda: FindDependencySymbolTool.apply(
        name_path="NetPackageManager"
    )
)
```

## Configuration

Dependency symbol search can be configured in your `serena_config.yml` or via the `DependencySymbolConfig` class:

```python
from serena.config.dependency_config import DependencySymbolConfig

config = DependencySymbolConfig(
    enabled=True,
    max_results=50,
    decompilation_enabled=True,
    decompiler_backend="ilspy", # or "cecil", "auto"
    external_search_paths=["/path/to/game/assemblies", "/path/to/mods"],
    include_system_assemblies=False
)
```

### Key Configuration Options

- **`external_search_paths`**: A list of paths to search for external DLLs. This is crucial for finding symbols in game assemblies or other non-standard locations.
- **`decompiler_backend`**: The decompilation engine to use. `"ilspy"` is recommended for best results.
- **`ilspycmd_path`**: The path to the `ilspycmd` executable. Defaults to `"ilspycmd"`, assuming it is in the system's PATH.
- **`decompilation_enabled`**: Must be `True` to enable symbol extraction from DLLs.

## Usage for Game Modding

To find symbols like `NetPackageManager` from a game's assemblies:

1.  **Configure `external_search_paths`**: Add the path to the game's managed assemblies directory to this list in your project configuration.
2.  **Enable Decompilation**: Set `decompilation_enabled` to `True`.
3.  **Use the Tool**: Call `FindDependencySymbolTool` with the name of the symbol you're looking for.

```python
# Example of finding a symbol in a game's assembly
result = agent.execute_task(
    lambda: FindDependencySymbolTool.apply("NetPackageManager")
)
```

## Implementation Details

### Decompiler Backends

Serena uses a pluggable decompiler system. The default is a placeholder implementation. For production use, you would integrate a real C# decompiler library.

-   **ILSpy**: Recommended for full decompilation. Requires a .NET interop bridge.
-   **Mono.Cecil**: A lightweight option for metadata-based symbol extraction.

The `decompiler_backend` configuration option allows you to choose the active backend.