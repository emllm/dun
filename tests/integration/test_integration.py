"""Integration tests for the Dun package."""
import subprocess
import sys
from unittest.mock import MagicMock, patch

from dun.llm_analyzer import LLMAnalyzer
from dun.processor_engine import ProcessorEngine


class TestIntegration:
    """Integration tests for the Dun package."""

    @patch('requests.get')
    @patch('requests.post')
    def test_full_flow(self, mock_post, mock_get, tmp_path, monkeypatch):
        """Test the full flow from natural language request to execution."""
        mock_get.return_value = MagicMock(status_code=200)
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

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        monkeypatch.setenv("OLLAMA_ENABLED", "true")
        monkeypatch.setenv("OUTPUT_DIR", str(output_dir))

        analyzer = LLMAnalyzer(base_url="http://test-ollama:11434")
        engine = ProcessorEngine(analyzer)

        with patch('subprocess.check_call') as mock_install:
            result = engine.process_natural_request(
                "Pobierz dane i zapisz w folderze wyjściowym"
            )

        assert result == {'status': 'test_success'}

        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == 'mistral:7b'
        assert "Pobierz dane i zapisz w folderze wyjściowym" in call_args['prompt']

        mock_install.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "pytest"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
