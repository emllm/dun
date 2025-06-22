"""Integration tests for the ProcessorEngine."""
import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from dun.core.engine import ProcessorEngine, ProcessingResult
from dun.services.processors import CSVProcessor
from dun.config.settings import get_settings

class TestProcessorEngineIntegration:
    """Integration tests for the ProcessorEngine."""

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
    def processor_engine(self):
        """Create a processor engine instance for testing."""
        engine = ProcessorEngine()
        # Don't automatically initialize to control when it happens in tests
        engine._initialized = False
        return engine
    
    @pytest.mark.asyncio
    async def test_initialize(self, processor_engine):
        """Test initializing the processor engine."""
        assert not processor_engine._initialized
        
        await processor_engine.initialize()
        
        assert processor_engine._initialized
        assert 'csv' in processor_engine._processors
        assert isinstance(processor_engine._processors['csv'], CSVProcessor)
    
    @pytest.mark.asyncio
    async def test_process_csv_combine(self, processor_engine, setup_test_files):
        """Test processing a CSV combine request."""
        await processor_engine.initialize()
        
        result = await processor_engine.process(
            "csv",
            {
                "input_path": setup_test_files['input_dir'],
                "output_path": setup_test_files['output_file']
            }
        )
        
        assert result.success
        assert "successfully processed" in result.message.lower()
        assert os.path.exists(setup_test_files['output_file'])
        
        # Verify the output file has combined data
        df = pd.read_csv(setup_test_files['output_file'])
        assert len(df) >= 2  # At least 2 rows from the test files
    
    @pytest.mark.asyncio
    async def test_process_natural_request_combine(self, processor_engine, setup_test_files):
        """Test processing a natural language combine request."""
        await processor_engine.initialize()
        
        # Set up the output file in the config
        processor_engine._processors['csv'].config.output_file = Path(setup_test_files['output_file'])
        
        result = await processor_engine.process_natural_request(
            f"Combine all CSV files in {setup_test_files['input_dir']}"
        )
        
        assert result.success
        assert "success" in result.message.lower()
        assert os.path.exists(setup_test_files['output_file'])
    
    @pytest.mark.asyncio
    async def test_process_natural_request_list(self, processor_engine, setup_test_files):
        """Test processing a natural language list files request."""
        await processor_engine.initialize()
        
        # Set up the input directory in the config
        processor_engine._processors['csv'].config.input_dir = Path(setup_test_files['input_dir'])
        
        result = await processor_engine.process_natural_request(
            "List all CSV files"
        )
        
        assert result.success
        assert "success" in result.message.lower()
        assert 'files' in result.data
        assert len(result.data['files']) == 2
    
    @pytest.mark.asyncio
    async def test_process_with_retry(self, processor_engine, setup_test_files):
        """Test processing with retry logic."""
        await processor_engine.initialize()
        
        # Mock the CSV processor to fail once then succeed
        original_method = processor_engine._processors['csv'].combine_csv_files
        
        async def mock_combine(*args, **kwargs):
            if not hasattr(mock_combine, '_failed'):
                mock_combine._failed = True
                raise Exception("Simulated temporary failure")
            return await original_method(*args, **kwargs)
        
        with patch.object(processor_engine._processors['csv'], 'combine_csv_files', new=mock_combine):
            result = await processor_engine.process(
                "csv",
                {
                    "input_path": setup_test_files['input_dir'],
                    "output_path": setup_test_files['output_file'],
                    "retry_attempts": 1
                }
            )
            
            assert result.success
            assert "successfully processed" in result.message.lower()
            assert os.path.exists(setup_test_files['output_file'])
    
    @pytest.mark.asyncio
    async def test_shutdown(self, processor_engine):
        """Test shutting down the processor engine."""
        await processor_engine.initialize()
        assert processor_engine._initialized
        
        await processor_engine.shutdown()
        assert not processor_engine._initialized
    
    @pytest.mark.asyncio
    async def test_health_status(self, processor_engine):
        """Test getting the health status."""
        status = processor_engine.get_health_status()
        assert 'initialized' in status
        assert 'processors' in status
        assert 'stats' in status
        assert 'timestamp' in status
        
        # Should be empty before initialization
        assert not status['initialized']
        assert not status['processors']
        
        # After initialization
        await processor_engine.initialize()
        status = processor_engine.get_health_status()
        assert status['initialized']
        assert 'csv' in status['processors']
        assert status['stats']['total_operations'] == 0
