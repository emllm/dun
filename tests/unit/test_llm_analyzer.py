"""Tests for LLMAnalyzer class."""
import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from dun.llm_analyzer import LLMAnalyzer, ProcessorConfig


class TestLLMAnalyzer:
    """Test cases for LLMAnalyzer."""

    @patch('requests.get')
    def test_check_ollama_connection_success(self, mock_get):
        """Test successful Ollama connection check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        analyzer = LLMAnalyzer()
        
        mock_get.assert_called_once_with("http://localhost:11434/api/tags")
        assert analyzer.base_url == "http://localhost:11434"

    @patch('requests.get')
    def test_check_ollama_connection_failure(self, mock_get):
        """Test failed Ollama connection check."""
        mock_get.side_effect = requests.RequestException("Connection error")
        
        # Should not raise an exception
        analyzer = LLMAnalyzer()
        
        assert analyzer.base_url == "http://localhost:11434"

    @patch('requests.post')
    def test_analyze_with_llm_success(self, mock_post):
        """Test successful LLM analysis."""
        # Mock response from LLM
        mock_response = {
            "response": """
            {
                "name": "test_processor",
                "description": "Test processor",
                "dependencies": [],
                "parameters": {},
                "code_template": "result = {'status': 'test_success'}"
            }
            """
        }
        
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status.return_value = None
        
        analyzer = LLMAnalyzer()
        result = analyzer._analyze_with_llm("test request")
        
        assert isinstance(result, ProcessorConfig)
        assert result.name == "test_processor"
        assert result.description == "Test processor"
        assert result.dependencies == []
        assert result.parameters == {}
        assert "result = {'status': 'test_success'}" in result.code_template

    @patch('requests.post')
    def test_analyze_with_llm_invalid_json(self, mock_post):
        """Test LLM analysis with invalid JSON response."""
        mock_response = {"response": "This is not a JSON"}
        mock_post.return_value.json.return_value = mock_response
        
        analyzer = LLMAnalyzer()
        
        with pytest.raises(ValueError, match="Nie znaleziono JSON w odpowiedzi LLM"):
            analyzer._analyze_with_llm("test request")

    @patch('requests.post')
    def test_analyze_request_llm_fallback(self, mock_post):
        """Test fallback to default processor when LLM fails."""
        mock_post.side_effect = requests.RequestException("API error")
        
        analyzer = LLMAnalyzer()
        result = analyzer.analyze_request("test request")
        
        assert result.name == "csv_processor"
        assert "pandas" in result.dependencies

    def test_get_default_imap_processor(self):
        """Test getting default processor config (now CSV)."""
        analyzer = LLMAnalyzer()
        config = analyzer._get_default_imap_processor()
        
        assert config.name == "csv_processor"
        assert "pandas" in config.dependencies
        assert "csv" in config.code_template.lower()
