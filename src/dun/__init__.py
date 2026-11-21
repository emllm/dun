"""Dun - Data Understanding and Navigation.

A powerful tool for data processing and analysis with natural language interface
and automatic environment diagnostics.
"""
from dun.app import DunApplication, run
from dun.config.settings import get_settings, settings
from dun.config_generator import ConfigGenerator, TaskConfigGenerator
from dun.core.contexts import ApplicationContext, get_context
from dun.env_definitions import EnvVariable
from dun.interactive_mapper import InteractiveMapper
from dun.library_catalog import LibraryInterface
from dun.packages import (
    dist_to_module,
    is_module_available,
    module_to_dist,
)
from dun.routing import (
    LexicalRouter,
    Route,
    fold,
    keyword_hits,
    library_router,
    task_router,
    tokens,
)
from dun.services.filesystem import FileSystemService, fs
from dun.services.ollama import OllamaService, ollama_service
from dun.smart_env_manager import SmartEnvManager
from dun.task_validator import TaskConfiguration, TaskValidator, ValidationResult

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
    "DunApplication",
    "run",
    "get_settings",
    "get_context",
    # Routing and consolidated task tooling
    "LexicalRouter",
    "Route",
    "fold",
    "tokens",
    "keyword_hits",
    "task_router",
    "library_router",
    "TaskConfigGenerator",
    "ConfigGenerator",
    "TaskValidator",
    "TaskConfiguration",
    "ValidationResult",
    "InteractiveMapper",
    "LibraryInterface",
    "SmartEnvManager",
    "EnvVariable",
    "dist_to_module",
    "module_to_dist",
    "is_module_available",
    # Services
    "FileSystemService",
    "fs",
    "OllamaService",
    "ollama_service",
    # Models and types
    "ApplicationContext",
    "settings",
    "context",
    # Version and metadata
    "__version__",
    "__author__",
    "__license__",
]
