"""Tests for the CSV processor service."""
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from dun.services.processors.csv_processor import CSVProcessor, CSVProcessingError
from dun.config.settings import get_settings

class TestCSVProcessor:
    """Test cases for the CSV processor service."""

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
        file1 = os.path.join(input_dir, "file1.csv")
        file2 = os.path.join(input_dir, "file2.csv")
        
        with open(file1, 'w') as f:
            f.write(test_data1)
        with open(file2, 'w') as f:
            f.write(test_data2)
        
        # Create output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        yield {
            'temp_dir': temp_dir,
            'input_dir': input_dir,
            'output_dir': output_dir,
            'file1': file1,
            'file2': file2,
            'output_file': os.path.join(output_dir, 'combined.csv')
        }
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def csv_processor(self):
        """Create a CSV processor instance for testing."""
        return CSVProcessor()
    
    @pytest.mark.asyncio
    async def test_find_csv_files(self, setup_test_files, csv_processor):
        """Test finding CSV files in a directory."""
        # Test with default input directory (should be empty)
        with pytest.raises(FileNotFoundError):
            await csv_processor.find_csv_files()
        
        # Test with our test directory
        csv_processor.config.input_dir = Path(setup_test_files['input_dir'])
        files = await csv_processor.find_csv_files()
        
        assert len(files) == 2
        assert any('file1.csv' in str(f) for f in files)
        assert any('file2.csv' in str(f) for f in files)
    
    @pytest.mark.asyncio
    async def test_read_csv(self, setup_test_files, csv_processor):
        """Test reading a CSV file."""
        df = await csv_processor.read_csv(setup_test_files['file1'])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['id', 'name', 'value']
        assert df['id'].tolist() == [1, 2]
        assert df['name'].tolist() == ['test', 'example']
        assert df['value'].tolist() == [100, 200]
    
    @pytest.mark.asyncio
    async def test_combine_csv_files(self, setup_test_files, csv_processor):
        """Test combining multiple CSV files."""
        # Set up config
        csv_processor.config.input_dir = Path(setup_test_files['input_dir'])
        csv_processor.config.output_file = Path(setup_test_files['output_file'])
        
        # Test combining files
        output_file = await csv_processor.combine_csv_files()
        
        assert os.path.exists(output_file)
        
        # Verify combined data
        df = pd.read_csv(output_file)
        assert len(df) == 4  # 2 rows from each file
        assert set(df.columns) == {'id', 'name', 'value', 'description', 'amount', '_source_file'}
        
        # Verify source file tracking
        assert df['_source_file'].nunique() == 2
    
    @pytest.mark.asyncio
    async def test_combine_csv_files_with_specific_files(self, setup_test_files, csv_processor):
        """Test combining specific CSV files."""
        output_file = Path(setup_test_files['output_file'])
        
        # Test combining specific files
        result = await csv_processor.combine_csv_files(
            file_paths=[setup_test_files['file1']],
            output_file=output_file
        )
        
        assert result == output_file
        assert os.path.exists(output_file)
        
        # Verify only file1 data is present
        df = pd.read_csv(output_file)
        assert len(df) == 2
        assert set(df.columns) == {'id', 'name', 'value', '_source_file'}
    
    @pytest.mark.asyncio
    async def test_combine_csv_files_with_nonexistent_dir(self, csv_processor):
        """Test combining files from a non-existent directory."""
        csv_processor.config.input_dir = Path("/nonexistent/directory")
        
        with pytest.raises(FileNotFoundError):
            await csv_processor.combine_csv_files()
    
    @pytest.mark.asyncio
    async def test_process_csv_request_combine(self, setup_test_files, csv_processor):
        """Test processing a combine request."""
        csv_processor.config.input_dir = Path(setup_test_files['input_dir'])
        csv_processor.config.output_file = Path(setup_test_files['output_file'])
        
        result = await csv_processor.process_csv_request("combine all csv files")
        
        assert result["status"] == "success"
        assert "combined" in result["message"].lower()
        assert os.path.exists(result["output_file"])
        
        # Verify the output file has combined data
        df = pd.read_csv(result["output_file"])
        assert len(df) >= 2  # At least 2 rows from the test files
    
    @pytest.mark.asyncio
    async def test_process_csv_request_list(self, setup_test_files, csv_processor):
        """Test processing a list files request."""
        csv_processor.config.input_dir = Path(setup_test_files['input_dir'])
        
        result = await csv_processor.process_csv_request("list all csv files")
        
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["files"]) == 2
        assert any('file1.csv' in f for f in result["files"])
        assert any('file2.csv' in f for f in result["files"])
    
    @pytest.mark.asyncio
    async def test_process_csv_request_unknown(self, csv_processor):
        """Test processing an unknown request."""
        result = await csv_processor.process_csv_request("some unknown request")
        
        assert result["status"] == "error"
        assert "not determine" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_combine_csv_files_with_invalid_file(self, setup_test_files, csv_processor):
        """Test combining files with an invalid CSV file."""
        # Create an invalid CSV file
        invalid_file = os.path.join(setup_test_files['input_dir'], 'invalid.csv')
        with open(invalid_file, 'w') as f:
            f.write("not,a,valid,csv,file")
        
        # This should not raise an exception but log an error
        result = await csv_processor.combine_csv_files(
            file_paths=[setup_test_files['file1'], invalid_file],
            output_file=setup_test_files['output_file']
        )
        
        # Should still process the valid file
        df = pd.read_csv(result)
        assert len(df) >= 2  # At least the rows from the valid file
