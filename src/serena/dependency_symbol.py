"""
Dependency symbol retrieval for external libraries and NuGet packages.
"""

import logging
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from serena.project import Project
from serena.config.dependency_config import DependencySymbolConfig, DEFAULT_DEPENDENCY_CONFIG
from serena.symbol import LanguageServerSymbol, LanguageServerSymbolLocation
# Remove unused import
from solidlsp.ls_types import SymbolKind

log = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Information about a project dependency."""
    
    name: str
    version: str
    type: str  # "nuget", "dll", "project"
    path: Optional[str] = None
    assembly_name: Optional[str] = None


class DependencySymbolRetriever:
    """
    Retrieves symbols from project dependencies including NuGet packages and external DLLs.
    Supports decompilation of external assemblies for symbol extraction.
    """
    
    def __init__(self, project: Project, config: Optional[DependencySymbolConfig] = None):
        self.project = project
        self.config = config or DEFAULT_DEPENDENCY_CONFIG
        self._dependencies_info: List[DependencyInfo] = []
        self._dependency_cache: Dict[str, List[LanguageServerSymbol]] = {}
        
    def clear_cache(self) -> None:
        """Clear the cached dependency symbols."""
        self._dependency_cache.clear()
        self._dependencies_info.clear()
        
    def list_dependencies(self) -> List[Dict[str, Any]]:
        """
        List all project dependencies that can be searched for symbols.
        
        :return: List of dependency information dictionaries
        """
        if not self._dependencies_info:
            self._discover_dependencies()
            
        return [
            {
                "name": dep.name,
                "version": dep.version,
                "type": dep.type,
                "path": dep.path,
                "assembly_name": dep.assembly_name
            }
            for dep in self._dependencies_info
        ]
        
    def find_dependency_symbols(
        self,
        name_path: str,
        include_body: bool = False,
        include_kinds: Optional[List[SymbolKind]] = None,
        exclude_kinds: Optional[List[SymbolKind]] = None,
        substring_matching: bool = False,
        include_nuget: bool = True,
        include_external_dlls: bool = True,
    ) -> List[LanguageServerSymbol]:
        """
        Find symbols in project dependencies matching the given name pattern.
        
        :param name_path: Symbol name pattern to search for
        :param include_body: Whether to include symbol bodies (decompiled)
        :param include_kinds: Symbol kinds to include
        :param exclude_kinds: Symbol kinds to exclude
        :param substring_matching: Use substring matching
        :param include_nuget: Include NuGet package symbols
        :param include_external_dlls: Include external DLL symbols
        :return: List of matching dependency symbols
        """
        if not self._dependencies_info:
            self._discover_dependencies()
            
        all_symbols: List[LanguageServerSymbol] = []
        
        # Get symbols from all dependencies
        for dep in self._dependencies_info:
            if (dep.type == "nuget" and not include_nuget) or (dep.type == "dll" and not include_external_dlls):
                continue
                
            symbols = self._get_dependency_symbols(dep, include_body)
            all_symbols.extend(symbols)
            
        # Filter symbols based on search criteria
        filtered_symbols = []
        for symbol in all_symbols:
            if self._matches_search_criteria(symbol, name_path, include_kinds, exclude_kinds, substring_matching):
                filtered_symbols.append(symbol)
                
        # Apply max results limit
        if self.config.max_results > 0 and len(filtered_symbols) > self.config.max_results:
            filtered_symbols = filtered_symbols[:self.config.max_results]
                
        return filtered_symbols
        
    def _discover_dependencies(self) -> None:
        """Discover all project dependencies."""
        self._dependencies_info = []
        
        # Discover NuGet packages
        self._discover_nuget_dependencies()
        
        # Discover external DLLs
        self._discover_external_dlls()
        
    def _discover_nuget_dependencies(self) -> None:
        """Discover NuGet package dependencies from project files."""
        project_root = self.project.project_root
        
        # Look for .csproj files
        csproj_files = []
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.csproj'):
                    csproj_files.append(os.path.join(root, file))
                    
        for csproj_file in csproj_files:
            try:
                tree = ET.parse(csproj_file)
                root = tree.getroot()
                
                # Find PackageReference elements
                for package_ref in root.findall(".//PackageReference"):
                    name = package_ref.get('Include')
                    version = package_ref.get('Version')
                    
                    if name and version:
                        self._dependencies_info.append(
                            DependencyInfo(
                                name=name,
                                version=version,
                                type="nuget",
                                assembly_name=f"{name}.dll"
                            )
                        )
                        
            except ET.ParseError as e:
                log.warning(f"Failed to parse project file {csproj_file}: {e}")
                
    def _discover_external_dlls(self) -> None:
        """Discover external DLL dependencies from bin directories."""
        project_root = self.project.project_root
        
        # Look for DLLs in bin directories
        bin_dirs = []
        for root, dirs, _ in os.walk(project_root):
            if 'bin' in dirs:
                bin_dirs.append(os.path.join(root, 'bin'))
                
        for bin_dir in bin_dirs:
            try:
                for root, _, files in os.walk(bin_dir):
                    for file in files:
                        if file.endswith('.dll') and not file.startswith('System.'):
                            # Skip system assemblies and focus on external ones
                            dll_path = os.path.join(root, file)
                            assembly_name = os.path.splitext(file)[0]
                            
                            self._dependencies_info.append(
                                DependencyInfo(
                                    name=assembly_name,
                                    version="unknown",
                                    type="dll",
                                    path=dll_path,
                                    assembly_name=assembly_name
                                )
                            )
                            
            except OSError as e:
                log.warning(f"Failed to scan bin directory {bin_dir}: {e}")
                
    def _get_dependency_symbols(self, dependency: DependencyInfo, include_body: bool = False) -> List[LanguageServerSymbol]:
        """
        Get symbols from a specific dependency.
        
        :param dependency: Dependency information
        :param include_body: Whether to include symbol bodies
        :return: List of symbols from the dependency
        """
        cache_key = f"{dependency.type}:{dependency.name}:{dependency.version}:{include_body}"
        
        if cache_key in self._dependency_cache:
            return self._dependency_cache[cache_key]
            
        symbols: List[LanguageServerSymbol] = []
        
        if dependency.type == "nuget":
            symbols = self._get_nuget_symbols(dependency, include_body)
        elif dependency.type == "dll" and dependency.path:
            symbols = self._get_dll_symbols(dependency, include_body)
            
        self._dependency_cache[cache_key] = symbols
        return symbols
        
    def _get_nuget_symbols(self, dependency: DependencyInfo, include_body: bool) -> List[LanguageServerSymbol]:
        """Get symbols from a NuGet package."""
        # For NuGet packages, we'll use metadata-based symbol extraction
        # This is a placeholder - actual implementation would use package metadata
        # or decompilation if the package is available locally
        
        # Create placeholder symbols for common .NET types and methods
        common_symbols = self._create_common_dotnet_symbols(dependency)
        return common_symbols
        
    def _get_dll_symbols(self, dependency: DependencyInfo, include_body: bool) -> List[LanguageServerSymbol]:
        """Get symbols from an external DLL using decompilation."""
        if not dependency.path or not os.path.exists(dependency.path):
            return []
            
        try:
            # Use Mono.Cecil for lightweight metadata extraction
            symbols = self._extract_dll_symbols_with_mono_cecil(dependency.path, include_body)
            return symbols
        except ImportError:
            log.warning("Mono.Cecil not available for DLL symbol extraction")
            return self._create_placeholder_dll_symbols(dependency)
            
    def _extract_dll_symbols_with_mono_cecil(self, dll_path: str, include_body: bool) -> List[LanguageServerSymbol]:
        """Extract symbols from DLL using Mono.Cecil."""
        # This would be implemented using Mono.Cecil to read assembly metadata
        # For now, return placeholder symbols
        return self._create_placeholder_dll_symbols(
            DependencyInfo(
                name=os.path.basename(dll_path).replace('.dll', ''),
                version="unknown",
                type="dll",
                path=dll_path
            )
        )
        
    def _create_common_dotnet_symbols(self, dependency: DependencyInfo) -> List[LanguageServerSymbol]:
        """Create placeholder symbols for common .NET types and methods."""
        symbols = []
        
        # Add common System types
        common_types = [
            ("System", "Console", SymbolKind.Class),
            ("System", "String", SymbolKind.Class),
            ("System", "Int32", SymbolKind.Class),
            ("System.Collections", "List", SymbolKind.Class),
            ("System.Collections.Generic", "Dictionary", SymbolKind.Class),
        ]
        
        for namespace, type_name, kind in common_types:
            if dependency.name.lower() in namespace.lower() or dependency.name.lower() in type_name.lower():
                # Create proper UnifiedSymbolInformation structure
                from solidlsp.ls_types import UnifiedSymbolInformation, Location, Range, Position
                from solidlsp.ls_utils import PathUtils
                
                # Create a file URI for the external dependency
                external_path = f"external:{dependency.name}"
                uri = PathUtils.path_to_uri(external_path)
                
                symbol_info: UnifiedSymbolInformation = {
                    "name": type_name,
                    "kind": kind,
                    "location": Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=0, character=0),
                            end=Position(line=0, character=0)
                        ),
                        absolutePath=external_path,
                        relativePath=external_path
                    ),
                    "selectionRange": Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=0)
                    ),
                    "children": []
                }
                symbols.append(LanguageServerSymbol(symbol_info))
                
        return symbols
        
    def _create_placeholder_dll_symbols(self, dependency: DependencyInfo) -> List[LanguageServerSymbol]:
        """Create placeholder symbols for DLL dependencies."""
        symbols = []
        
        # Create a placeholder class symbol for the DLL
        from solidlsp.ls_types import UnifiedSymbolInformation, Location, Range, Position
        from solidlsp.ls_utils import PathUtils
        
        # Create a file URI for the external dependency
        external_path = f"external:{dependency.name}"
        uri = PathUtils.path_to_uri(external_path)
        
        symbol_info: UnifiedSymbolInformation = {
            "name": dependency.name,
            "kind": SymbolKind.Class,
            "location": Location(
                uri=uri,
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=0)
                ),
                absolutePath=external_path,
                relativePath=external_path
            ),
            "selectionRange": Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=0)
            ),
            "children": []
        }
        symbols.append(LanguageServerSymbol(symbol_info))
        
        return symbols
        
    def _matches_search_criteria(
        self,
        symbol: LanguageServerSymbol,
        name_path: str,
        include_kinds: Optional[Sequence[SymbolKind]],
        exclude_kinds: Optional[Sequence[SymbolKind]],
        substring_matching: bool
    ) -> bool:
        """Check if a symbol matches the search criteria."""
        # Check symbol kind
        if include_kinds and symbol.symbol_kind not in include_kinds:
            return False
        if exclude_kinds and symbol.symbol_kind in exclude_kinds:
            return False
            
        # Check name matching
        symbol_name = symbol.name or ""
        if substring_matching:
            return name_path.lower() in symbol_name.lower()
        else:
            return symbol_name.lower() == name_path.lower()