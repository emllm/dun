"""Tests for CSV processor functionality."""
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pandas as pd
import pytest

from dun.llm_analyzer import LLMAnalyzer, ProcessorConfig
from dun.processor_engine import ProcessorEngine


class MockLLMAnalyzer:
    """Mock LLMAnalyzer for testing."""
    
    def analyze_request(self, request):
        return LLMAnalyzer()._get_csv_processor()
    
    def _get_csv_processor(self):
        return LLMAnalyzer()._get_csv_processor()


class TestCSVProcessor:
    """Test cases for CSV processing functionality."""

    @pytest.fixture
    def setup_test_files(self):
        """Set up test files and directories."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="dun_test_")
        
        # Create test CSV files
        test_data1 = """id,name,value
1,test,100
2,example,200"""
        
        test_data2 = """id,description,amount
3,item one,10.5
4,item two,20.75"""
        
        # Create input directory
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir, exist_ok=True)
        
        # Write test files
        with open(os.path.join(input_dir, "file1.csv"), 'w') as f:
            f.write(test_data1)
        
        with open(os.path.join(input_dir, "file2.csv"), 'w') as f:
            f.write(test_data2)
        
        # Create output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        yield {
            'temp_dir': temp_dir,
            'input_dir': input_dir,
            'output_dir': output_dir,
            'output_file': os.path.join(output_dir, 'combined.csv')
        }
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_csv_processor_combine_files(self, setup_test_files):
        """Test combining multiple CSV files into one."""
        test_data = setup_test_files
        
        # Create a mock LLMAnalyzer that returns our CSV processor config
        mock_llm_analyzer = MockLLMAnalyzer()
        
        # Create processor engine with the mock analyzer
        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        
        # Set output directory in environment for the test
        os.environ['OUTPUT_DIR'] = test_data['output_dir']
        os.environ['INPUT_DIR'] = test_data['input_dir']
        
        # Process the request
        result = processor.process_natural_request("process csv files")
        
        # Verify the output file was created
        assert os.path.exists(test_data['output_file'])
        
        # Verify the combined data
        df = pd.read_csv(test_data['output_file'])
        assert len(df) == 4  # 2 rows from each file
        assert set(df.columns) == {'id', 'name', 'value', 'description', 'amount'}
        assert df['id'].tolist() == [1, 2, 3, 4]

    def test_csv_processor_empty_directory(self, tmp_path):
        """Test behavior with empty input directory."""
        # Create an empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        # Create a mock analyzer
        mock_llm_analyzer = MockLLMAnalyzer()
        
        # Create processor engine
        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        
        # Set input directory in environment for the test
        os.environ['INPUT_DIR'] = str(empty_dir)
        
        # This should raise an error
        with pytest.raises(ValueError, match="Nie znaleziono plików CSV"):
            with patch.dict(os.environ, {'INPUT_DIR': str(empty_dir)}):
                processor.process_natural_request("process csv files")

    def test_csv_processor_permission_error(self, setup_test_files, monkeypatch):
        """Test behavior when output directory is not writable."""
        test_data = setup_test_files
        
        # Create mock analyzer
        mock_llm_analyzer = MockLLMAnalyzer()
        
        # Create processor engine
        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        
        # Set input directory in environment for the test
        os.environ['INPUT_DIR'] = test_data['input_dir']
        
        # Make output directory read-only
        os.chmod(test_data['output_dir'], 0o444)
        
        # Create processor engine
        processor = ProcessorEngine()
        
        # This should still work because it will fall back to temp directory
        result = processor.process_natural_request("process csv files")
        
        # The result should contain a temporary file path
        assert 'output_file' in result
        assert 'tmp' in result['output_file'] or 'temp' in result['output_file']
        
        # Clean up read-only directory
        os.chmod(test_data['output_dir'], 0o755)

    def test_csv_processor_invalid_files(self, tmp_path):
        """Test behavior with invalid CSV files."""
        # Create a directory with an invalid CSV
        test_dir = tmp_path / "test_invalid"
        test_dir.mkdir()
        
        # Create an invalid CSV file
        invalid_csv = test_dir / "invalid.csv"
        invalid_csv.write_text("not,a,csv,file")
        
        # Create mock analyzer
        mock_llm_analyzer = MockLLMAnalyzer()
        
        # Create processor engine
        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        
        # Set input directory in environment for the test
        os.environ['INPUT_DIR'] = str(test_dir)
        
        # This should raise an error when trying to process the invalid file
        with pytest.raises(Exception):
            processor.process_natural_request("process csv files")
