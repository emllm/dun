"""Integration tests for example use cases from EXAMPLE.md."""
import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from loguru import logger

# Import the LLMAnalyzer and other necessary components
from dun.llm_analyzer import LLMAnalyzer

# Test data directory path
TEST_DATA_DIR = Path(__file__).parent / "test_data"

@pytest.fixture
def setup_test_environment():
    """Set up test environment with necessary directories and mocks."""
    # Create test data directory if it doesn't exist
    TEST_DATA_DIR.mkdir(exist_ok=True)
    
    # Set up any necessary environment variables
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:21434"
    
    yield  # Test runs here
    
    # Cleanup after tests if needed
    # Remove any test files created during tests
    for file in TEST_DATA_DIR.glob("test_*"):
        try:
            file.unlink()
        except Exception as e:
            logger.warning(f"Could not remove test file {file}: {e}")

# Mock responses for LLM to simulate different scenarios
MOCK_LLM_RESPONSES = {
    "imap": {
        "name": "imap_processor",
        "description": "Process IMAP emails and save to folders",
        "dependencies": ["imaplib", "email"],
        "parameters": {
            "server": "imap.example.com",
            "username": "${IMAP_USERNAME}",
            "password": "${IMAP_PASSWORD}",
            "mailbox": "INBOX"
        },
        "code_template": """
import imaplib
import email
from pathlib import Path

# Connect to IMAP server
mail = imaplib.IMAP4_SSL('${server}')
mail.login('${username}', '${password}')
mail.select('${mailbox}')

# Search and process emails
result, data = mail.search(None, 'ALL')
email_ids = data[0].split()

for email_id in email_ids:
    # Process each email
    pass
        """
    },
    "csv_analysis": {
        "name": "csv_analyzer",
        "description": "Analyze CSV files and generate statistics",
        "dependencies": ["pandas", "numpy"],
        "parameters": {
            "input_dir": "data/",
            "output_file": "analysis_report.txt"
        },
        "code_template": """
import pandas as pd
import numpy as np
from pathlib import Path

# Read and process CSV files
# ... (implementation details)
        """
    },
    "web_scraping": {
        "name": "web_scraper",
        "description": "Scrape articles from news website",
        "dependencies": ["requests", "beautifulsoup4"],
        "parameters": {
            "url": "https://news.com",
            "output_file": "articles.json"
        },
        "code_template": """
import requests
from bs4 import BeautifulSoup
import json

# Scrape website and extract articles
# ... (implementation details)
        """
    }
}

def mock_llm_response(*args, **kwargs):
    """Mock LLM response based on the prompt content."""
    prompt = kwargs.get('json', {}).get('prompt', '').lower()
    
    if 'imap' in prompt or 'email' in prompt or 'wiadomości' in prompt:
        return MagicMock(
            status_code=200,
            json=lambda: {"response": json.dumps(MOCK_LLM_RESPONSES["imap"])}
        )
    elif 'csv' in prompt or 'analiz' in prompt or 'statyst' in prompt:
        return MagicMock(
            status_code=200,
            json=lambda: {"response": json.dumps(MOCK_LLM_RESPONSES["csv_analysis"])}
        )
    elif 'web' in prompt or 'scrap' in prompt or 'stron' in prompt:
        return MagicMock(
            status_code=200,
            json=lambda: {"response": json.dumps(MOCK_LLM_RESPONSES["web_scraping"])}
        )
    
    # Default response
    return MagicMock(
        status_code=200,
        json=lambda: {"response": "{}"}
    )

@patch('requests.post', side_effect=mock_llm_response)
def test_imap_email_processing(mock_post):
    """Test IMAP email processing integration."""
    # Arrange
    analyzer = LLMAnalyzer()
    request = "Pobierz wszystkie wiadomości email ze skrzynki IMAP i zapisz je w folderach uporządkowanych według roku i miesiąca"
    
    # Act
    config = analyzer.analyze_request(request)
    
    # Assert
    assert config.name == "imap_processor"
    assert "imaplib" in config.dependencies
    assert "email" in config.dependencies
    assert "server" in config.parameters
    assert "${IMAP_USERNAME}" in config.parameters.values()
    assert "${IMAP_PASSWORD}" in config.parameters.values()
    assert "mail.select('${mailbox}')" in config.code_template

@patch('requests.post', side_effect=mock_llm_response)
def test_csv_analysis_processing(mock_post):
    """Test CSV analysis integration."""
    # Arrange
    analyzer = LLMAnalyzer()
    request = "Przeanalizuj wszystkie pliki CSV w folderze data/, połącz je w jeden dataset i wygeneruj raport z podstawowymi statystykami"
    
    # Act
    config = analyzer.analyze_request(request)
    
    # Assert
    assert config.name == "csv_analyzer"
    assert "pandas" in config.dependencies
    assert "numpy" in config.dependencies
    assert "input_dir" in config.parameters
    assert "output_file" in config.parameters

@patch('requests.post', side_effect=mock_llm_response)
def test_web_scraping_processing(mock_post):
    """Test web scraping integration."""
    # Arrange
    analyzer = LLMAnalyzer()
    request = "Pobierz wszystkie artykuły z strony news.com, wyodrębnij tytuły i treść, a następnie zapisz w formacie JSON"
    
    # Act
    config = analyzer.analyze_request(request)
    
    # Assert
    assert config.name == "web_scraper"
    assert "requests" in config.dependencies
    assert "beautifulsoup4" in config.dependencies
    assert "url" in config.parameters
    assert "output_file" in config.parameters
    assert "https://news.com" in config.parameters.values()

def test_llm_fallback_behavior():
    """Test fallback behavior when LLM is not available."""
    # Arrange
    analyzer = LLMAnalyzer()
    request = "Some request"
    
    # Mock a failed LLM response
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("LLM service unavailable")
        
        # Act
        config = analyzer.analyze_request(request)
        
        # Assert that we get a default config when LLM fails
        assert config is not None
        assert hasattr(config, 'name')
        assert hasattr(config, 'dependencies')
        assert hasattr(config, 'parameters')
        assert hasattr(config, 'code_template')
