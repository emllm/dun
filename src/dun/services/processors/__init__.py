"""Data processors for different file formats and operations."""
from typing import Optional, Dict, Any

from .csv_processor import CSVProcessor, csv_processor, CSVProcessingError

__all__ = [
    'CSVProcessor',
    'csv_processor',
    'CSVProcessingError',
]

def get_processor(processor_type: str, config: Optional[Dict[str, Any]] = None):
    """Get a processor instance by type."""
    processors = {
        'csv': CSVProcessor,
    }
    
    processor_class = processors.get(processor_type.lower())
    if not processor_class:
        raise ValueError(f"Unknown processor type: {processor_type}")
    
    return processor_class(**(config or {}))
