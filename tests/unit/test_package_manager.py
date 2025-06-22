"""Tests for DynamicPackageManager class."""
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from dun.processor_engine import DynamicPackageManager


class TestDynamicPackageManager:
    """Test cases for DynamicPackageManager."""

    @patch('subprocess.check_call')
    def test_install_package_success(self, mock_check_call):
        """Test successful package installation."""
        manager = DynamicPackageManager()
        result = manager.install_package("test-package")
        
        assert result is True
        mock_check_call.assert_called_once()
        assert "test-package" in manager.installed_packages

    @patch('subprocess.check_call')
    def test_install_already_installed(self, mock_check_call):
        """Test installing an already installed package."""
        manager = DynamicPackageManager()
        manager.installed_packages.add("test-package")
        
        result = manager.install_package("test-package")
        
        assert result is True
        mock_check_call.assert_not_called()

    @patch('subprocess.check_call')
    def test_install_package_failure(self, mock_check_call):
        """Test package installation failure."""
        mock_check_call.side_effect = subprocess.CalledProcessError(1, "pip install test-package")
        manager = DynamicPackageManager()
        
        result = manager.install_package("test-package")
        
        assert result is False
        assert "test-package" not in manager.installed_packages

    @patch('importlib.import_module')
    def test_import_module_success(self, mock_import_module):
        """Test successful module import without needing installation."""
        mock_module = MagicMock()
        mock_import_module.return_value = mock_module
        
        manager = DynamicPackageManager()
        with patch.object(manager, 'install_package', return_value=True) as mock_install:
            result = manager.import_module("test_module")
        
        assert result == mock_module
        mock_import_module.assert_called_once_with("test_module")
        # install_package should not be called if import succeeds on first try
        mock_install.assert_not_called()

    @patch('importlib.import_module')
    def test_import_module_install_failure(self, mock_import_module):
        """Test module import when installation fails."""
        mock_import_module.side_effect = ImportError
        manager = DynamicPackageManager()
        
        with patch.object(manager, 'install_package', return_value=False) as mock_install:
            with pytest.raises(ImportError):
                manager.import_module("nonexistent_module")
        
        mock_install.assert_called_once_with("nonexistent_module")
