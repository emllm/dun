"""Integration tests for the Dun package."""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dun.llm_analyzer import LLMAnalyzer
from dun.core.engine.processor_engine import ProcessorEngine


class TestIntegration:
    """Integration tests for the Dun package."""

    @patch('requests.post')
    def test_full_flow(self, mock_post, tmp_path):
        """Test the full flow from natural language request to execution."""
        # Mock the LLM response
        mock_response = {
            "response": """
            {
                "name": "test_processor",
                "description": "Test processor",
                "dependencies": ["pytest"],
                "parameters": {"test_param": "value"},
                "code_template": "result = {'status': 'test_success'}"
            }
            """
        }
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status.return_value = None
        
        # Create test output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Initialize components
        with patch('os.getenv', return_value=str(output_dir)):
            analyzer = LLMAnalyzer(base_url="http://test-ollama:11434")
            engine = ProcessorEngine(analyzer)
        
        # Mock package installation
        with patch('subprocess.check_call') as mock_install:
            # Process the request
            result = engine.process_natural_request(
                "Pobierz dane i zapisz w folderze wyjściowym"
            )
        
        # Verify the result
        assert result == {'status': 'test_success'}
        
        # Verify LLM was called with the right parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == 'mistral:7b'
        assert "Pobierz dane i zapisz w folderze wyjściowym" in call_args['prompt']
        
        # Verify package installation was attempted
        mock_install.assert_called_once_with([
            sys.executable, "-m", "pip", "install", "pytest"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
