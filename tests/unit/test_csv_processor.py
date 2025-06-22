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
        os.environ['INPUT_DIR'] = test_data['input_dir']
        
        # Process the request
        result = processor.process_natural_request("process csv files")
        
        # Since we're using a temporary directory for output, we need to find the temp file
        # Look for the most recently created file in any dun_csv_* subdirectory
        import tempfile
        import glob
        import time
        
        # Wait a moment to ensure the file is written
        time.sleep(0.5)
        
        # Search for the file in all dun_csv_* subdirectories
        temp_dir = tempfile.gettempdir()
        pattern = os.path.join(temp_dir, 'dun_csv_*', 'combined.csv')
        temp_files = glob.glob(pattern)
        
        # If not found, try a more general search
        if not temp_files:
            temp_files = []
            for root, dirs, files in os.walk(temp_dir):
                if 'combined.csv' in files and 'dun_csv_' in root:
                    temp_files.append(os.path.join(root, 'combined.csv'))
        
        # Sort by modification time to get the most recent
        temp_files.sort(key=os.path.getmtime, reverse=True)
        
        # The most recent temp file should be our output
        assert len(temp_files) > 0, f"No temporary output file found matching {pattern}"
        output_file = temp_files[0]
        
        # Verify the file exists and has content
        assert os.path.exists(output_file), f"Output file {output_file} does not exist"
        assert os.path.getsize(output_file) > 0, f"Output file {output_file} is empty"
        
        # Check if output file was created and has content
        assert os.path.exists(output_file), f"Output file was not created at {output_file}"
        assert os.path.getsize(output_file) > 0, "Output file is empty"
        
        # Check if output file has expected content
        with open(output_file, 'r') as f:
            lines = f.readlines()
            
        # Check header contains all expected columns (order doesn't matter)
        header = lines[0].strip().split(',')
        expected_columns = {'id', 'name', 'value', 'description', 'amount'}
        assert set(header) == expected_columns, f"Header {header} does not match expected columns {expected_columns}"
        
        # Check data rows (convert to sets to ignore order)
        content = '\n'.join(lines)
        assert 'item one' in content and '10.5' in content, "Output file does not contain expected data from file2"
        assert 'item two' in content and '20.75' in content, "Output file does not contain expected data from file2"
        assert 'test' in content and '100' in content, "Output file does not contain expected data from file1"
        assert 'example' in content and '200' in content, "Output file does not contain expected data from file1"

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
        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        
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
