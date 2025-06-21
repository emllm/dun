"""Test configuration and fixtures."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dun.llm_analyzer import LLMAnalyzer, ProcessorConfig
from dun.processor_engine import ProcessorEngine, DynamicPackageManager


@pytest.fixture
def mock_llm_analyzer():
    """Create a mock LLM analyzer."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        analyzer = LLMAnalyzer(base_url="http://test-ollama:11434")
        
    # Mock the analyze_request method
    analyzer.analyze_request = MagicMock(return_value=ProcessorConfig(
        name="test_processor",
        description="Test processor",
        dependencies=[],
        parameters={},
        code_template="result = {'status': 'test_success'}"
    ))
    
    return analyzer


@pytest.fixture
def processor_engine(mock_llm_analyzer):
    """Create a processor engine with a mock LLM analyzer."""
    return ProcessorEngine(mock_llm_analyzer)


@pytest.fixture
dynamic_package_manager():
    """Create a dynamic package manager with mocked methods."""
    manager = DynamicPackageManager()
    manager.install_package = MagicMock(return_value=True)
    manager.import_module = MagicMock(return_value=MagicMock())
    return manager
