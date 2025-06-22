"""Tests for ProcessorEngine class."""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

import pytest

from dun.processor_engine import ProcessorEngine, ProcessorConfig, DynamicPackageManager


class TestProcessorEngine:
    """Test cases for ProcessorEngine."""

    @patch('os.getenv')
    def test_init_default_output_dir(self, mock_getenv, tmp_path, mock_llm_analyzer):
        """Test initialization with default output directory."""
        # Mock getenv to return None for OUTPUT_DIR
        mock_getenv.return_value = None
        
        # Create a temporary directory and change to it for the test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Test that the output directory is created in the current working directory
            engine = ProcessorEngine(mock_llm_analyzer)
            
            expected_dir = Path.cwd() / "output"
            assert engine.output_dir == expected_dir
            assert engine.output_dir.exists()
            assert engine.output_dir.is_dir()
        finally:
            # Restore the original working directory
            os.chdir(original_cwd)

    @patch('os.getenv')
    def test_init_custom_output_dir(self, mock_getenv, tmp_path, mock_llm_analyzer):
        """Test initialization with custom output directory."""
        custom_dir = tmp_path / "custom_output"
        
        # Mock getenv to return our custom directory
        def getenv_side_effect(key, default=None):
            if key == "OUTPUT_DIR":
                return str(custom_dir)
            return os.environ.get(key, default)
            
        mock_getenv.side_effect = getenv_side_effect
        
        # The directory shouldn't exist yet
        assert not custom_dir.exists()
        
        # Create the engine, which should create the directory
        engine = ProcessorEngine(mock_llm_analyzer)
        
        # Verify the directory was created and is accessible
        assert engine.output_dir == custom_dir
        assert engine.output_dir.exists()
        assert engine.output_dir.is_dir()

    @patch('dun.processor_engine.exec')
    def test_execute_processor_success(self, mock_exec, processor_engine, tmp_path):
        """Test successful processor execution."""
        # Setup test config
        config = ProcessorConfig(
            name="test_processor",
            description="Test processor",
            dependencies=[],
            parameters={"test_param": "value"},
            code_template="result = {'status': 'success'}"
        )
        
        # Create a test output directory
        output_dir = tmp_path / "test_output"
        output_dir.mkdir()
        
        # Patch the output_dir of the processor_engine
        processor_engine.output_dir = output_dir
        
        # Mock the execution context
        mock_context = {}
        
        def exec_side_effect(code, context):
            # Update the context with expected values
            context.update({
                'result': {'status': 'test_success'},
                'os': os,
                'Path': Path,
                'logger': MagicMock(),
                'output_dir': str(output_dir),
                'package_manager': MagicMock()
            })
            
        mock_exec.side_effect = exec_side_effect
        
        # Execute the processor
        result = processor_engine._execute_processor(config)
        
        # Verify the result
        assert result == {'status': 'test_success'}
        mock_exec.assert_called_once()
        
        # Get the actual context passed to exec
        call_args = mock_exec.call_args[0]
        assert call_args[0] == config.code_template
        
        # Check if required context variables are present
        context = call_args[1]
        assert 'os' in context
        assert 'sys' in context
        assert 'Path' in context
        assert 'logger' in context
        assert 'output_dir' in context
        assert context['output_dir'] == str(output_dir)
        assert 'package_manager' in context

    @patch('dun.processor_engine.exec')
    def test_execute_processor_exception(self, mock_exec, processor_engine):
        """Test processor execution with exception."""
        config = ProcessorConfig(
            name="failing_processor",
            description="Failing processor",
            dependencies=[],
            parameters={},
            code_template="raise ValueError('Test error')"
        )
        
        mock_exec.side_effect = ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            processor_engine._execute_processor(config)

    @patch.object(ProcessorEngine, '_execute_processor')
    def test_process_natural_request(self, mock_execute, processor_engine, mock_llm_analyzer):
        """Test processing a natural language request."""
        # Setup mock
        mock_config = MagicMock()
        mock_config.dependencies = []
        mock_llm_analyzer.analyze_request.return_value = mock_config
        mock_execute.return_value = {'status': 'test_success'}
        
        # Test the method
        result = processor_engine.process_natural_request("test request")
        
        # Verify the result and calls
        assert result == {'status': 'test_success'}
        mock_llm_analyzer.analyze_request.assert_called_once_with("test request")
        mock_execute.assert_called_once_with(mock_config)
        
        # Test with dependencies
        mock_config.dependencies = ['test_package']
        with patch.object(processor_engine.package_manager, 'install_package') as mock_install:
            mock_install.return_value = True
            processor_engine.process_natural_request("test request with deps")
            mock_install.assert_called_once_with('test_package')
