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
            decompilation_enabled=True,
            include_nuget_packages=True,
            include_external_dlls=True,
            external_search_paths=[os.path.join(self.temp_dir, "external_libs")]
        )
        
        self.retriever = DependencySymbolRetriever(self.project, self.config)
        
        # Create a dummy external lib for testing
        self.external_lib_path = os.path.join(self.temp_dir, "external_libs")
        os.makedirs(self.external_lib_path, exist_ok=True)
        with open(os.path.join(self.external_lib_path, "NetPackageManager.dll"), "w") as f:
            f.write("dummy dll content")


    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test that the retriever initializes correctly."""
        self.assertEqual(self.retriever.project, self.project)
        self.assertEqual(self.retriever.config, self.config)
        self.assertIsNotNone(self.retriever._decompiler)

    def test_clear_cache(self):
        """Test that cache clearing works correctly."""
        # Add some dummy data to cache
        mock_symbol = Mock()
        self.retriever._dependency_cache["test"] = [mock_symbol]
        self.retriever.clear_cache()
        self.assertEqual(len(self.retriever._dependency_cache), 0)

    @patch('serena.dependency_symbol.DependencySymbolRetriever._discover_nuget_dependencies')
    def test_discover_external_dlls(self, mock_discover_nuget):
        """Test discovery of external DLLs."""
        self.retriever._discover_dependencies()
        
        dll_deps = [dep for dep in self.retriever._dependencies_info if dep.type == "dll"]
        self.assertEqual(len(dll_deps), 1)
        self.assertEqual(dll_deps[0].name, "NetPackageManager")
        
    @patch('serena.dependency_decompiler.IlSpyDecompiler.enumerate_types')
    def test_find_dependency_symbols_with_decompiler(self, mock_enumerate_types):
        """Test finding symbols using the decompiler."""
        mock_enumerate_types.return_value = ["NetPackageManager"]
        
        symbols = self.retriever.find_dependency_symbols("NetPackageManager")
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0].name, "NetPackageManager")

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