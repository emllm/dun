"""Tests for ProcessorEngine class."""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

import pytest

from dun.processor_engine import ProcessorEngine, ProcessorConfig, DynamicPackageManager


class TestProcessorEngine:
    """Test cases for ProcessorEngine."""

    def test_init_default_output_dir(self, tmp_path, mock_llm_analyzer):
        """Test initialization with default output directory."""
        with patch('os.getenv', return_value=None):
            engine = ProcessorEngine(mock_llm_analyzer)
            
        assert engine.output_dir == Path.cwd() / "output"
        assert engine.output_dir.exists()

    def test_init_custom_output_dir(self, tmp_path, mock_llm_analyzer):
        """Test initialization with custom output directory."""
        custom_dir = tmp_path / "custom_output"
        with patch('os.getenv', return_value=str(custom_dir)):
            engine = ProcessorEngine(mock_llm_analyzer)
            
        assert engine.output_dir == custom_dir
        assert engine.output_dir.exists()

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
        
        # Mock the execution context
        mock_context = {}
        
        def exec_side_effect(code, context):
            context.update({
                'result': {'status': 'test_success'},
                'os': os,
                'Path': Path,
                'logger': MagicMock(),
                'output_dir': str(tmp_path),
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
