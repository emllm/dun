"""Tests for CSV processor functionality."""
import os
import shutil
import tempfile

import pytest

from dun.llm_analyzer import LLMAnalyzer
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

    def test_csv_processor_combine_files(self, setup_test_files, monkeypatch):
        """Test combining multiple CSV files into one."""
        test_data = setup_test_files

        mock_llm_analyzer = MockLLMAnalyzer()
        monkeypatch.setenv('INPUT_DIR', test_data['input_dir'])
        monkeypatch.setenv('OUTPUT_DIR', test_data['output_dir'])
        monkeypatch.setenv('OUTPUT_FILE', test_data['output_file'])
        monkeypatch.setenv('OLLAMA_ENABLED', 'false')

        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        result = processor.process_natural_request("process csv files")

        output_file = result['output_file']
        assert output_file == test_data['output_file']
        assert os.path.exists(output_file), f"Output file {output_file} does not exist"
        assert os.path.getsize(output_file) > 0, f"Output file {output_file} is empty"

        with open(output_file, 'r') as f:
            lines = f.readlines()

        header = lines[0].strip().split(',')
        expected_columns = {'id', 'name', 'value', 'description', 'amount'}
        assert set(header) == expected_columns

        content = '\n'.join(lines)
        assert 'item one' in content and '10.5' in content
        assert 'item two' in content and '20.75' in content
        assert 'test' in content and '100' in content
        assert 'example' in content and '200' in content

    def test_csv_processor_empty_directory(self, tmp_path, monkeypatch):
        """Test behavior with empty input directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        mock_llm_analyzer = MockLLMAnalyzer()
        monkeypatch.setenv('INPUT_DIR', str(empty_dir))
        monkeypatch.setenv('OUTPUT_DIR', str(out_dir))
        monkeypatch.setenv('OUTPUT_FILE', str(out_dir / "combined.csv"))

        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        with pytest.raises(ValueError, match="Nie znaleziono plików CSV"):
            processor.process_natural_request("process csv files")

    def test_csv_processor_permission_error(self, setup_test_files, monkeypatch):
        """Test behavior when output directory is not writable."""
        test_data = setup_test_files

        mock_llm_analyzer = MockLLMAnalyzer()
        monkeypatch.setenv('INPUT_DIR', test_data['input_dir'])
        monkeypatch.setenv('OUTPUT_DIR', test_data['output_dir'])
        monkeypatch.setenv('OUTPUT_FILE', test_data['output_file'])

        os.chmod(test_data['output_dir'], 0o555)
        try:
            processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
            result = processor.process_natural_request("process csv files")

            assert 'output_file' in result
            assert 'tmp' in result['output_file'] or 'temp' in result['output_file']
            assert os.path.exists(result['output_file'])
        finally:
            os.chmod(test_data['output_dir'], 0o755)
            out = result.get('output_file') if 'result' in locals() else None
            if out and os.path.exists(out):
                shutil.rmtree(os.path.dirname(out), ignore_errors=True)

    def test_csv_processor_invalid_files(self, tmp_path, monkeypatch):
        """Test behavior with invalid CSV files."""
        test_dir = tmp_path / "test_invalid"
        test_dir.mkdir()
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        invalid_csv = test_dir / "invalid.csv"
        invalid_csv.write_text("not,a,csv,file")

        mock_llm_analyzer = MockLLMAnalyzer()
        monkeypatch.setenv('INPUT_DIR', str(test_dir))
        monkeypatch.setenv('OUTPUT_DIR', str(out_dir))
        monkeypatch.setenv('OUTPUT_FILE', str(out_dir / "combined.csv"))

        processor = ProcessorEngine(llm_analyzer=mock_llm_analyzer)
        with pytest.raises(Exception):
            processor.process_natural_request("process csv files")
