"""Context management system for the application.

This module provides a way to manage application-wide state and dependencies
using a context-based approach.
"""
from typing import Any, Dict, Optional, Type, TypeVar, cast
from ..protocols import ContextProtocol, ServiceProtocol

T = TypeVar('T')

class ApplicationContext:
    """Main application context that holds all services and state."""
    
    def __init__(self):
        self._services: Dict[str, ServiceProtocol] = {}
        self._state: Dict[str, Any] = {}
    
    def register_service(self, service: ServiceProtocol) -> None:
        """Register a service with the context."""
        self._services[service.name] = service
    
    def get_service(self, name: str) -> Optional[ServiceProtocol]:
        """Get a registered service by name."""
        return self._services.get(name)
    
    def get_service_by_type(self, service_type: Type[T]) -> Optional[T]:
        """Get a service by its type."""
        for service in self._services.values():
            if isinstance(service, service_type):
                return cast(T, service)
        return None
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a state value."""
        self._state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self._state.get(key, default)
    
    async def initialize_services(self) -> None:
        """Initialize all registered services."""
        for service in self._services.values():
            if hasattr(service, 'initialize') and callable(service.initialize):
                await service.initialize()
    
    async def shutdown(self) -> None:
        """Shut down all registered services."""
        for service in reversed(list(self._services.values())):
            if hasattr(service, 'shutdown') and callable(service.shutdown):
                await service.shutdown()

# Global application context
app_context: Optional[ApplicationContext] = None

def get_context() -> ApplicationContext:
    """Get the global application context, creating it if necessary."""
    global app_context
    if app_context is None:
        app_context = ApplicationContext()
    return app_context

def set_context(context: ApplicationContext) -> None:
    """Set the global application context."""
    global app_context
    app_context = context
