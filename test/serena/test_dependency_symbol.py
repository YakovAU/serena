"""
Tests for dependency symbol search functionality.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from serena.dependency_symbol import DependencySymbolRetriever, DependencyInfo
from serena.config.dependency_config import DependencySymbolConfig
from serena.project import Project
from serena.config.serena_config import ProjectConfig
from solidlsp.ls_config import Language
from solidlsp.ls_types import SymbolKind


class TestDependencySymbolRetriever(unittest.TestCase):
    """Test cases for DependencySymbolRetriever."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary project directory
        self.temp_dir = tempfile.mkdtemp()
        project_config = ProjectConfig(
            project_name="test_project",
            language=Language.CSHARP
        )
        self.project = Project(self.temp_dir, project_config=project_config)
        
        # Create a mock config
        self.config = DependencySymbolConfig(
            enabled=True,
            max_results=10,
            decompilation_enabled=False,
            include_nuget_packages=True,
            include_external_dlls=True
        )
        
        self.retriever = DependencySymbolRetriever(self.project, self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test that the retriever initializes correctly."""
        self.assertEqual(self.retriever.project, self.project)
        self.assertEqual(self.retriever.config, self.config)
        self.assertEqual(len(self.retriever._dependencies_info), 0)
        self.assertEqual(len(self.retriever._dependency_cache), 0)

    def test_clear_cache(self):
        """Test that cache clearing works correctly."""
        # Add some dummy data to cache
        mock_symbol = Mock()
        self.retriever._dependency_cache["test"] = [mock_symbol]
        self.retriever.clear_cache()
        self.assertEqual(len(self.retriever._dependency_cache), 0)

    @patch('serena.dependency_symbol.DependencySymbolRetriever._discover_nuget_dependencies')
    @patch('serena.dependency_symbol.DependencySymbolRetriever._discover_external_dlls')
    def test_discover_dependencies(self, mock_discover_dlls, mock_discover_nuget):
        """Test dependency discovery."""
        self.retriever._discover_dependencies()
        mock_discover_nuget.assert_called_once()
        mock_discover_dlls.assert_called_once()

    def test_matches_search_criteria_basic(self):
        """Test basic search criteria matching."""
        # Create a mock symbol
        mock_symbol = Mock()
        mock_symbol.symbol_kind = SymbolKind.Class
        mock_symbol.get_name_path.return_value = "TestClass"
        
        # Test exact match
        result = self.retriever._matches_search_criteria(
            mock_symbol, "TestClass", None, None, False
        )
        self.assertTrue(result)
        
        # Test substring match
        result = self.retriever._matches_search_criteria(
            mock_symbol, "Test", None, None, True
        )
        self.assertTrue(result)
        
        # Test no match
        result = self.retriever._matches_search_criteria(
            mock_symbol, "OtherClass", None, None, False
        )
        self.assertFalse(result)

    def test_matches_search_criteria_with_kinds(self):
        """Test search criteria with kind filtering."""
        # Create a mock symbol
        mock_symbol = Mock()
        mock_symbol.symbol_kind = SymbolKind.Class
        
        # Test include kinds
        result = self.retriever._matches_search_criteria(
            mock_symbol, "Test", [SymbolKind.Class], None, True
        )
        self.assertTrue(result)
        
        # Test exclude kinds
        result = self.retriever._matches_search_criteria(
            mock_symbol, "Test", None, [SymbolKind.Class], True
        )
        self.assertFalse(result)

    @patch('serena.dependency_symbol.DependencySymbolRetriever._get_dependency_symbols')
    def test_find_dependency_symbols_empty(self, mock_get_symbols):
        """Test finding symbols with no dependencies."""
        mock_get_symbols.return_value = []
        
        symbols = self.retriever.find_dependency_symbols("Test")
        self.assertEqual(len(symbols), 0)

    def test_create_common_dotnet_symbols(self):
        """Test creation of common .NET symbols."""
        dependency = DependencyInfo(
            name="System",
            version="4.0.0",
            type="nuget"
        )
        
        symbols = self.retriever._create_common_dotnet_symbols(dependency)
        self.assertGreater(len(symbols), 0)
        
        # Check that we have some common System types
        symbol_names = [symbol.name for symbol in symbols]
        self.assertIn("Console", symbol_names)
        self.assertIn("String", symbol_names)

    def test_create_placeholder_dll_symbols(self):
        """Test creation of placeholder DLL symbols."""
        dependency = DependencyInfo(
            name="TestLibrary",
            version="1.0.0",
            type="dll"
        )
        
        symbols = self.retriever._create_placeholder_dll_symbols(dependency)
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0].name, "TestLibrary")

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        valid_config = DependencySymbolConfig()
        valid_config.validate()  # Should not raise
        
        # Invalid configs
        invalid_config = DependencySymbolConfig(max_results=0)
        with self.assertRaises(ValueError):
            invalid_config.validate()
            
        invalid_config = DependencySymbolConfig(decompilation_depth=3)
        with self.assertRaises(ValueError):
            invalid_config.validate()
            
        invalid_config = DependencySymbolConfig(min_confidence_threshold=1.5)
        with self.assertRaises(ValueError):
            invalid_config.validate()


if __name__ == '__main__':
    unittest.main()