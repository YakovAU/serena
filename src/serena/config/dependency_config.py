"""
Configuration for dependency symbol search functionality.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class DependencySymbolConfig:
    """
    Configuration for dependency symbol search and decompilation.
    """
    
    # General settings
    enabled: bool = True
    """Whether dependency symbol search is enabled."""
    
    max_results: int = 50
    """Maximum number of dependency symbols to return in a single search."""
    
    # Decompilation settings
    decompilation_enabled: bool = False
    """Whether to attempt decompilation of external assemblies."""
    
    decompilation_depth: int = 1
    """Depth of decompilation (0 = metadata only, 1 = basic, 2 = full)."""
    
    include_private_members: bool = False
    """Whether to include private members in decompiled symbols."""
    
    # Cache settings
    cache_enabled: bool = True
    """Whether to cache dependency symbols for better performance."""
    
    cache_ttl_seconds: int = 3600
    """Time-to-live for cached dependency symbols in seconds."""
    
    # Scope settings
    include_nuget_packages: bool = True
    """Whether to include symbols from NuGet packages."""
    
    include_external_dlls: bool = True
    """Whether to include symbols from external DLLs."""
    
    include_system_assemblies: bool = False
    """Whether to include symbols from system assemblies (e.g., System.*)."""
    
    # Decompiler backend selection
    decompiler_backend: str = "ilspy"
    """Decompiler backend to use: "ilspy", "cecil", or "auto" (prefers ilspy if available)."""

    ilspycmd_path: str = "ilspycmd"
    """Path to the ilspycmd executable."""

    # External dependencies search paths
    external_search_paths: List[str] = field(default_factory=list)
    """Additional locations to search for external DLLs (relative or absolute)."""

    # Filter settings
    min_confidence_threshold: float = 0.7
    """Minimum confidence threshold for symbol matching (0.0 to 1.0)."""
    
    def validate(self) -> None:
        """Validate the configuration values."""
        if self.max_results < 1:
            raise ValueError("max_results must be at least 1")
        if self.decompilation_depth < 0 or self.decompilation_depth > 2:
            raise ValueError("decompilation_depth must be between 0 and 2")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        if not 0.0 <= self.min_confidence_threshold <= 1.0:
            raise ValueError("min_confidence_threshold must be between 0.0 and 1.0")


# Default configuration
DEFAULT_DEPENDENCY_CONFIG = DependencySymbolConfig()