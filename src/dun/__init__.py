"""Dun - Data Understanding and Navigation.

A powerful tool for data processing and analysis with natural language interface
and automatic environment diagnostics.
"""
from dun.app import DunApplication, run
from dun.config.settings import get_settings, settings
from dun.core.contexts import ApplicationContext, get_context
from dun.services.filesystem import FileSystemService, fs
from dun.services.ollama import OllamaService, ollama_service

# Package metadata
__version__ = "0.2.0"
__author__ = "Tom Sapletta <info@softreck.dev>"
__license__ = "Apache-2.0"

# Initialize default services
context: ApplicationContext = get_context()
context.register_service(FileSystemService())
context.register_service(OllamaService())

__all__ = [
    # Core components
    'DunApplication',
    'run',
    'get_settings',
    'get_context',
    
    # Services
    'FileSystemService',
    'fs',
    'OllamaService',
    'ollama_service',
    
    # Models and types
    'ApplicationContext',
    'settings',
    'context',
    
    # Version and metadata
    '__version__',
    '__author__',
    '__license__',
]