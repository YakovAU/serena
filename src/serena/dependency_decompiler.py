"""
Dependency decompiler backends for external assemblies.

This module provides a pluggable interface to decompile external DLLs
and NuGet assemblies. The backends are designed to be production-friendly
front-ends that can be swapped or extended without changing the caller
code paths in DependencySymbolRetriever.

Note:
- In a full production environment, ILSpy (ICSharpCode.Decompiler) would be
  used as the primary decompiler backend, likely via a .NET interop bridge.
- Cecil (Mono.Cecil) can provide metadata-based symbol extraction with no
  decompilation when depth=0 or minimal bodies are requested.
- This Python-based placeholder is designed for integration without hard
  dependencies. It provides a clear extension point for real backends.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

log = logging.getLogger(__name__)


class DecompilerBackend(ABC):
    """
    Abstract interface for decompiler backends.
    """

    def __init__(self, depth: int = 1, include_private_members: bool = False) -> None:
        self.depth = depth
        self.include_private_members = include_private_members

    @abstractmethod
    def enumerate_types(self, assembly_path: str) -> List[str]:
        """
        Enumerate available type names from the given assembly.
        Returns a list of fully-qualified type names, e.g. "Namespace.Type".
        """
        raise NotImplementedError

    @abstractmethod
    def decompile_type_body(self, assembly_path: str, type_name: str) -> str:
        """
        Return the decompiled body for a specific type, or an informative stub
        if decompilation isn't available for that type.
        """
        raise NotImplementedError


class IlSpyDecompiler(DecompilerBackend):
    """
    ILSpy-based decompiler backend (production-ready integration would wrap the
    .NET ICSharpCode.Decompiler library). This is a placeholder implementation
    to enable a clean integration point in Python code.
    """

    def __init__(self, depth: int = 1, include_private_members: bool = False) -> None:
        super().__init__(depth=depth, include_private_members=include_private_members)

    def enumerate_types(self, assembly_path: str) -> List[str]:
        log.info("IlSpyDecompiler: enumerate_types called for %s", assembly_path)
        # Placeholder: real implementation would invoke ILSpy ICSharpCode.Decompiler
        # to enumerate types. Returning empty list indicates no types discovered
        # in this placeholder path.
        return []

    def decompile_type_body(self, assembly_path: str, type_name: str) -> str:
        # Placeholder decompilation body
        return f"// Decompiled body of {type_name} from {assembly_path} [ILSpy placeholder]"


class CecilDecompiler(DecompilerBackend):
    """
    Mono.Cecil-based decompiler (metadata-based). This is a placeholder backend
    for environments where decompilation is not desired or available at runtime.
    """

    def __init__(self, depth: int = 1, include_private_members: bool = False) -> None:
        super().__init__(depth=depth, include_private_members=include_private_members)

    def enumerate_types(self, assembly_path: str) -> List[str]:
        log.info("CecilDecompiler: enumerate_types called for %s", assembly_path)
        # Placeholder: real implementation would read metadata via Cecil
        return []

    def decompile_type_body(self, assembly_path: str, type_name: str) -> str:
        return f"// Decompiled body of {type_name} from {assembly_path} [Cecil placeholder]"