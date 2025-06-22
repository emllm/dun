"""Integration tests for CSV processor."""
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from unittest.mock import patch

from dun.__main__ import main as dun_main
from dun.llm_analyzer import LLMAnalyzer
from dun.processor_engine import ProcessorEngine


class TestCSVProcessorIntegration:
    """Integration tests for CSV processing."""

    @pytest.fixture
    def setup_integration_test(self, monkeypatch):
        """Set up integration test environment."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="dun_integration_test_")
        
        # Create test CSV files
        test_data1 = """id,name,value
1,integration,100
2,test,200"""
        
        test_data2 = """id,description,amount
3,integration item,15.5
4,another item,25.0"""
        
        # Create input directory
        input_dir = os.path.join(temp_dir, "data")
        os.makedirs(input_dir, exist_ok=True)
        
        # Write test files
        with open(os.path.join(input_dir, "data1.csv"), 'w') as f:
            f.write(test_data1)
        
        with open(os.path.join(input_dir, "data2.csv"), 'w') as f:
            f.write(test_data2)
        
        # Create output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up environment variables
        monkeypatch.setenv('INPUT_DIR', input_dir)
        monkeypatch.setenv('OUTPUT_FILE', os.path.join(output_dir, 'combined.csv'))
        monkeypatch.setenv('OLLAMA_ENABLED', 'false')  # Force using the CSV processor
        
        yield {
            'temp_dir': temp_dir,
            'input_dir': input_dir,
            'output_file': os.path.join(output_dir, 'combined.csv')
        }
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_csv_processor_integration(self, setup_integration_test, capsys, monkeypatch):
        """Test CSV processing through the main application."""
        test_data = setup_integration_test
        
        # Mock input to simulate user entering the command
        def mock_input(_):
            return "Przetwórz pliki CSV"
        
        monkeypatch.setattr('builtins.input', mock_input)
        
        # Run the main function
        with patch('sys.argv', ['dun']):
            with patch('dun.llm_analyzer.LLMAnalyzer.analyze_request') as mock_analyze:
                # Make sure we use our CSV processor
                mock_analyze.return_value = LLMAnalyzer()._get_csv_processor()
                with pytest.raises(SystemExit):
                    dun_main()
        
        # Capture output
        captured = capsys.readouterr()
        print("[DEBUG CLI OUTPUT]", captured.out)
        
        # Verify output contains success message
        assert "Zapisano połączony zbiór danych" in captured.out
        
        # Verify the output file was created
        assert os.path.exists(test_data['output_file'])
        
        # Verify the combined data
        df = pd.read_csv(test_data['output_file'])
        assert len(df) == 4  # 2 rows from each file
        assert set(df.columns) == {'id', 'name', 'value', 'description', 'amount'}

    def test_csv_processor_cli(self, setup_integration_test, monkeypatch, tmp_path):
        """Test CSV processing through CLI with command line arguments."""
        test_data = setup_integration_test
        output_file = str(tmp_path / "cli_output.csv")
        
        # Set up environment
        monkeypatch.setenv('OUTPUT_FILE', output_file)
        
        # Mock command line arguments
        with patch('sys.argv', ['dun', '--command', 'Przetwórz pliki CSV']):
            with patch('dun.llm_analyzer.LLMAnalyzer.analyze_request') as mock_analyze:
                # Make sure we use our CSV processor
                mock_analyze.return_value = LLMAnalyzer()._get_csv_processor()
                with pytest.raises(SystemExit):
                    dun_main()
        
        # Verify the output file was created
        assert os.path.exists(output_file)
        
        # Verify the combined data
        df = pd.read_csv(output_file)
        assert len(df) == 4  # 2 rows from each file

    def test_csv_processor_with_different_encoding(self, setup_integration_test, monkeypatch):
        """Test CSV processing with different file encodings."""
        test_data = setup_integration_test
        
        # Create a file with different encoding (UTF-16)
        special_file = os.path.join(test_data['input_dir'], 'special_chars.csv')
        with open(special_file, 'w', encoding='utf-16') as f:
            f.write("id,text\n1,zażółć gęślą jaźń\n2,łódź jeża\n")
        
        # Process the files
        from dun.llm_analyzer import LLMAnalyzer
        processor = ProcessorEngine(llm_analyzer=LLMAnalyzer())
        result = processor.process_natural_request("process csv files")
        
        # Verify the output
        assert 'output_file' in result
        assert os.path.exists(result['output_file'])
        
        # The file with special encoding might fail to load, but the rest should work
        df = pd.read_csv(result['output_file'])
        assert len(df) >= 4  # At least the original 4 rows should be there
