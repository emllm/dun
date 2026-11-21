"""Processor engine for managing and executing data processing tasks."""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

from dun.config.settings import get_settings
from dun.core.contexts import get_context
from dun.core.protocols import ServiceProtocol
from dun.services.processors import CSVProcessingError, CSVProcessor

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ProcessorConfig')

class ProcessorConfig(BaseModel):
    """Base configuration for processors."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    processor_type: str = "base"
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None

    @field_validator('input_path', 'output_path', mode='before')
    @classmethod
    def validate_paths(cls, v):
        if v is None or isinstance(v, Path):
            return v
        return Path(str(v))


class ProcessingResult(BaseModel):
    """Result of a processing operation."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    output_path: Optional[Path] = None
    error: Optional[str] = None


class ProcessorEngine(ServiceProtocol):
    """Engine for managing and executing data processing tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.settings = get_settings()
        self.context = get_context()
        self._processors: Dict[str, Any] = {}
        self._initialized = False
        self._stats: Dict[str, int] = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Return current initialization, registered processors, and stats."""
        return {
            "initialized": self._initialized,
            "processors": list(self._processors.keys()),
            "stats": dict(self._stats),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @property
    def name(self) -> str:
        return "processor_engine"
    
    @property
    def is_available(self) -> bool:
        return True  # Always available
    
    async def initialize(self) -> None:
        """Initialize the processor engine and all registered processors."""
        if self._initialized:
            return
            
        # Register default processors
        self.register_processor("csv", CSVProcessor)
        
        # Initialize all processors
        for name, processor in self._processors.items():
            if hasattr(processor, 'initialize') and callable(processor.initialize):
                await processor.initialize()
        
        self._initialized = True
        logger.info("Processor engine initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the processor engine and all registered processors."""
        for name, processor in self._processors.items():
            if hasattr(processor, 'shutdown') and callable(processor.shutdown):
                try:
                    await processor.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down processor {name}: {e}")
        
        self._initialized = False
        logger.info("Processor engine shutdown complete")
    
    def register_processor(self, name: str, processor_class: Type) -> None:
        """Register a processor class."""
        if not isinstance(processor_class, type):
            raise ValueError(f"Expected a class, got {type(processor_class)}")
            
        self._processors[name.lower()] = processor_class()
        logger.debug(f"Registered processor: {name}")
    
    def get_processor(self, processor_type: str) -> Any:
        """Get a processor instance by type."""
        processor = self._processors.get(processor_type.lower())
        if not processor:
            raise ValueError(f"No processor registered for type: {processor_type}")
        return processor
    
    async def process(
        self,
        processor_type: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ProcessingResult:
        """Process data using the specified processor."""
        processor_config = dict(config or {})
        processor_config.update(kwargs)
        retry_attempts = max(0, int(processor_config.get("retry_attempts", 0) or 0))
        self._stats["total_operations"] += 1

        last_exc: Optional[Exception] = None
        for attempt in range(retry_attempts + 1):
            try:
                processor = self.get_processor(processor_type)

                if processor_type == "csv":
                    if processor_config.get("input_path"):
                        processor.config.input_dir = Path(str(processor_config["input_path"]))
                    if processor_config.get("output_path"):
                        processor.config.output_file = Path(str(processor_config["output_path"]))
                    if "request" in processor_config:
                        result = await processor.process_csv_request(processor_config["request"])
                        ok = result.get("status") == "success"
                        self._stats["successful_operations" if ok else "failed_operations"] += 1
                        return ProcessingResult(
                            success=ok,
                            message=result.get("message", ""),
                            data=result,
                            output_path=result.get("output_file")
                        )
                    output_file = await processor.combine_csv_files(
                        file_paths=processor_config.get("file_paths"),
                        output_file=processor_config.get("output_path") or processor_config.get("output_file")
                    )
                    self._stats["successful_operations"] += 1
                    return ProcessingResult(
                        success=True,
                        message=f"Successfully processed {processor_type} files",
                        output_path=output_file
                    )
                if hasattr(processor, 'process') and callable(processor.process):
                    result = await processor.process(processor_config)
                    self._stats["successful_operations"] += 1
                    return ProcessingResult(
                        success=True,
                        message=f"Successfully processed with {processor_type} processor",
                        data=result
                    )
                raise NotImplementedError(
                    f"Processor {processor_type} does not implement a process method"
                )
            except CSVProcessingError as e:
                last_exc = e
                if attempt >= retry_attempts:
                    self._stats["failed_operations"] += 1
                    return ProcessingResult(
                        success=False,
                        message=f"CSV processing error: {e}",
                        error=str(e)
                    )
            except Exception as e:
                last_exc = e
                logger.exception(f"Error in {processor_type} processor")
                if attempt >= retry_attempts:
                    self._stats["failed_operations"] += 1
                    return ProcessingResult(
                        success=False,
                        message=f"Error processing {processor_type} data: {e}",
                        error=str(e)
                    )
        self._stats["failed_operations"] += 1
        return ProcessingResult(success=False, message=str(last_exc or "Unknown error"), error=str(last_exc))
    
    async def process_natural_request(self, request: str) -> ProcessingResult:
        """Process a natural language request by determining the appropriate processor."""
        try:
            # Simple processor selection based on keywords
            # In a real implementation, this would use an LLM to determine the processor
            request_lower = request.lower()
            
            if any(keyword in request_lower for keyword in ["csv", "excel", "spreadsheet"]):
                return await self.process("csv", {"request": request})
            else:
                # Default to CSV processor with the request as is
                return await self.process("csv", {"request": request})
                
        except Exception as e:
            logger.exception("Error processing natural language request")
            return ProcessingResult(
                success=False,
                message=f"Error processing request: {e}",
                error=str(e)
            )


# Global processor engine instance
processor_engine = ProcessorEngine()
