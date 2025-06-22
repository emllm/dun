"""Protocol definitions for the MCP architecture.

This module defines the core interfaces that different components of the system
must implement to participate in the MCP architecture.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, runtime_checkable

T = TypeVar('T')

class ServiceProtocol(Protocol):
    """Base protocol for all services in the system."""
    
    @property
    def name(self) -> str:
        """Return the name of the service."""
        ...
    
    @property
    def is_available(self) -> bool:
        """Check if the service is available."""
        ...
    
    async def initialize(self) -> None:
        """Initialize the service."""
        ...
    
    async def shutdown(self) -> None:
        """Shut down the service."""
        ...


class DiagnosticResult:
    """Result of a diagnostic check."""
    
    def __init__(self, 
                 name: str, 
                 status: bool, 
                 message: str = "", 
                 details: Optional[Dict[str, Any]] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
    
    def __bool__(self) -> bool:
        return self.status
    
    def __str__(self) -> str:
        status = "✓" if self.status else "✗"
        return f"{status} {self.name}: {self.message}"


class DiagnosticProtocol(Protocol):
    """Protocol for diagnostic operations."""
    
    @property
    def name(self) -> str:
        """Return the name of the diagnostic."""
        ...
    
    async def run_checks(self) -> List[DiagnosticResult]:
        """Run diagnostic checks and return results."""
        ...


class ConfigProtocol(Protocol):
    """Protocol for configuration management."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        ...
    
    def load(self) -> None:
        """Load configuration from persistent storage."""
        ...
    
    def save(self) -> None:
        """Save configuration to persistent storage."""
        ...


class ContextProtocol(Protocol):
    """Protocol for context management."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the context."""
        ...
    
    def update(self, **kwargs: Any) -> None:
        """Update multiple values in the context."""
        ...
    
    def clear(self) -> None:
        """Clear the context."""
        ...


class ModelProtocol(Protocol[T]):
    """Protocol for data models."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelProtocol[T]':
        """Create a model instance from a dictionary."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        ...
    
    def validate(self) -> bool:
        """Validate the model data."""
        ...
