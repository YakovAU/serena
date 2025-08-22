"""
Dependency symbol search tools for external libraries and NuGet packages.
"""

import json
import logging
import os
from typing import Any

from serena.tools import (
    SUCCESS_RESULT,
    TOOL_DEFAULT_MAX_ANSWER_LENGTH,
    Tool,
    ToolMarkerSymbolicRead,
)
from serena.tools.tools_base import ToolMarkerOptional
from solidlsp.ls_types import SymbolKind

from .symbol_tools import _sanitize_symbol_dict

log = logging.getLogger(__name__)


class FindDependencySymbolTool(Tool, ToolMarkerSymbolicRead):
    """
    Performs a global search for symbols in project dependencies (NuGet packages and external DLLs).
    Supports searching for types, methods, and other symbols from external libraries.
    """

    def apply(
        self,
        name_path: str,
        include_body: bool = False,
        include_kinds: list[int] = [],
        exclude_kinds: list[int] = [],
        substring_matching: bool = False,
        include_nuget: bool = True,
        include_external_dlls: bool = True,
        max_answer_chars: int = TOOL_DEFAULT_MAX_ANSWER_LENGTH,
    ) -> str:
        """
        Retrieves information on symbols from project dependencies based on the given `name_path`.
        This tool searches through NuGet packages and external DLL references to find matching symbols.

        :param name_path: The name path pattern to search for (e.g., "Console.WriteLine", "System.Collections.List")
        :param include_body: If True, include the symbol's source code (decompiled if available)
        :param include_kinds: Optional. List of LSP symbol kind integers to include.
        :param exclude_kinds: Optional. List of LSP symbol kind integers to exclude.
        :param substring_matching: If True, use substring matching for the symbol name.
        :param include_nuget: If True, search symbols from NuGet package dependencies.
        :param include_external_dlls: If True, search symbols from external DLL references.
        :param max_answer_chars: Max characters for the JSON result. If exceeded, no content is returned.
        :return: a list of dependency symbols (with locations and metadata) matching the name.
        """
        parsed_include_kinds: list[SymbolKind] | None = [SymbolKind(k) for k in include_kinds] if include_kinds else None
        parsed_exclude_kinds: list[SymbolKind] | None = [SymbolKind(k) for k in exclude_kinds] if exclude_kinds else None
        
        # Get dependency symbol retriever
        dependency_retriever = self.create_dependency_symbol_retriever()
        
        symbols = dependency_retriever.find_dependency_symbols(
            name_path,
            include_body=include_body,
            include_kinds=parsed_include_kinds,
            exclude_kinds=parsed_exclude_kinds,
            substring_matching=substring_matching,
            include_nuget=include_nuget,
            include_external_dlls=include_external_dlls,
        )
        
        symbol_dicts = [_sanitize_symbol_dict(s.to_dict(kind=True, location=True, depth=0, include_body=include_body)) for s in symbols]
        result = json.dumps(symbol_dicts)
        return self._limit_length(result, max_answer_chars)


class ListDependenciesTool(Tool, ToolMarkerSymbolicRead):
    """
    Lists all dependencies (NuGet packages and external DLLs) available in the project.
    """

    def apply(
        self,
        max_answer_chars: int = TOOL_DEFAULT_MAX_ANSWER_LENGTH,
    ) -> str:
        """
        Lists all project dependencies that can be searched for symbols.

        :param max_answer_chars: Max characters for the JSON result. If exceeded, no content is returned.
        :return: a list of dependency information including name, version, and type.
        """
        dependency_retriever = self.create_dependency_symbol_retriever()
        dependencies = dependency_retriever.list_dependencies()
        
        result = json.dumps(dependencies)
        return self._limit_length(result, max_answer_chars)


class ClearDependencyCacheTool(Tool, ToolMarkerOptional):
    """
    Clears the dependency symbol cache, forcing re-scanning of dependencies.
    """

    def apply(self) -> str:
        """
        Clears the cached dependency symbols. Use this if dependencies have changed
        or if you want to force a fresh scan of all dependencies.
        """
        dependency_retriever = self.create_dependency_symbol_retriever()
        dependency_retriever.clear_cache()
        return SUCCESS_RESULT