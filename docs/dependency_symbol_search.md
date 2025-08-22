# Dependency Symbol Search

Serena now includes advanced dependency symbol search capabilities that allow you to search for symbols not just in your project code, but also in external dependencies like NuGet packages and DLLs.

## Overview

The dependency symbol search feature extends Serena's existing symbol search capabilities to include:

- **NuGet Packages**: Search for types and members in referenced NuGet packages
- **External DLLs**: Search for symbols in external DLL dependencies
- **System Assemblies**: Optionally include symbols from system assemblies
- **Decompilation Support**: Lightweight decompilation for better symbol information

## Available Tools

### FindDependencySymbolTool

The main tool for searching dependency symbols:

```python
from serena.tools import FindDependencySymbolTool

# Search for Console type in dependencies
result = agent.execute_task(
    lambda: FindDependencySymbolTool.apply(
        name_path="Console",
        include_nuget=True,
        include_external_dlls=True
    )
)
```

**Parameters:**
- `name_path`: Symbol name pattern to search for
- `include_body`: Include decompiled source code (default: False)
- `include_kinds`: Filter by symbol kinds (e.g., [5] for classes only)
- `exclude_kinds`: Exclude specific symbol kinds
- `substring_matching`: Use substring matching (default: False)
- `include_nuget`: Include NuGet package symbols (default: True)
- `include_external_dlls`: Include external DLL symbols (default: True)
- `max_answer_chars`: Maximum response length

### Enhanced LanguageServerSymbolRetriever

The existing `LanguageServerSymbolRetriever` now includes a new method:

```python
symbol_retriever = agent.create_language_server_symbol_retriever()

# Search including dependencies
symbols = symbol_retriever.find_with_dependencies(
    name_path="List",
    include_dependencies=True,
    include_nuget=True,
    include_external_dlls=True
)
```

## Configuration

Dependency symbol search can be configured using `DependencySymbolConfig`:

```python
from serena.config.dependency_config import DependencySymbolConfig

config = DependencySymbolConfig(
    enabled=True,
    max_results=50,
    decompilation_enabled=False,
    decompilation_depth=1,
    include_private_members=False,
    cache_enabled=True,
    cache_ttl_seconds=3600,
    include_nuget_packages=True,
    include_external_dlls=True,
    include_system_assemblies=False,
    min_confidence_threshold=0.7
)
```

### Configuration Options

- **enabled**: Enable/disable dependency symbol search
- **max_results**: Maximum number of symbols to return
- **decompilation_enabled**: Enable decompilation for better symbol info
- **decompilation_depth**: 0=metadata only, 1=basic, 2=full decompilation
- **include_private_members**: Include private members in results
- **cache_enabled**: Enable caching for better performance
- **cache_ttl_seconds**: Cache time-to-live in seconds
- **include_nuget_packages**: Include NuGet package symbols
- **include_external_dlls**: Include external DLL symbols
- **include_system_assemblies**: Include system assembly symbols
- **min_confidence_threshold**: Minimum match confidence (0.0-1.0)

## Usage Examples

### Basic Dependency Search

```python
# Find all Console references in dependencies
result = agent.execute_task(
    lambda: FindDependencySymbolTool.apply("Console")
)
```

### Filtered Search

```python
# Find only classes in dependencies
result = agent.execute_task(
    lambda: FindDependencySymbolTool.apply(
        name_path="List",
        include_kinds=[5],  # Class kind
        include_nuget=True,
        include_external_dlls=False
    )
)
```

### With Decompilation

```python
# Get symbols with decompiled source
result = agent.execute_task(
    lambda: FindDependencySymbolTool.apply(
        name_path="StringBuilder",
        include_body=True,
        decompilation_enabled=True
    )
)
```

## Integration with Existing Tools

The dependency symbol search integrates seamlessly with existing Serena tools:

1. **Combined Results**: `find_with_dependencies()` returns both project and dependency symbols
2. **Consistent API**: Same parameter structure as existing symbol tools
3. **Caching**: Shared caching mechanism with project symbols
4. **Error Handling**: Graceful fallback when dependencies are unavailable

## Implementation Details

### Symbol Extraction Methods

1. **NuGet Packages**: Uses package metadata and common .NET type knowledge
2. **External DLLs**: Uses Mono.Cecil for metadata extraction and optional decompilation
3. **System Assemblies**: Placeholder symbols for common system types

### Caching Strategy

- **Per-dependency caching**: Each dependency is cached separately
- **TTL-based expiration**: Configurable cache duration
- **Memory efficient**: Only caches symbol metadata, not full decompiled content

### Performance Considerations

- **Lazy loading**: Dependencies are discovered on first use
- **Selective decompilation**: Only decompile when requested
- **Configurable limits**: Maximum results and depth controls

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure project has proper NuGet references
2. **Decompilation Errors**: Install Mono.Cecil for better DLL support
3. **Performance Issues**: Adjust cache settings and max results

### Debug Mode

Enable debug logging to see dependency discovery and symbol extraction:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Planned improvements for dependency symbol search:

- [ ] Full decompilation support with ILSpy integration
- [ ] Better NuGet package metadata extraction
- [ ] Symbol cross-referencing between dependencies
- [ ] Advanced filtering and ranking
- [ ] Visual Studio integration for dependency discovery

## See Also

- [Symbol Tools Documentation](symbol_tools.md)
- [Language Server Integration](language_server.md)
- [Configuration Guide](configuration.md)