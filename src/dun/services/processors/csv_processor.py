"""CSV Processor service for handling CSV file operations."""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import pandas as pd
from pydantic import BaseModel, Field, validator

from dun.core.protocols import ServiceProtocol
from dun.services.filesystem import fs
from dun.config.settings import get_settings

logger = logging.getLogger(__name__)

class CSVProcessorConfig(BaseModel):
    """Configuration for CSV Processor."""
    input_dir: Path = Field(default_factory=lambda: Path("data"))
    output_file: Optional[Path] = None
    output_dir: Path = Field(default_factory=lambda: Path("output"))
    delimiter: str = ","
    encoding: str = "utf-8"
    include_header: bool = True
    
    @validator('input_dir', 'output_dir', pre=True)
    def ensure_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v


class CSVProcessingError(Exception):
    """Exception raised for errors in CSV processing."""
    pass


class CSVProcessor(ServiceProtocol):
    """Service for processing CSV files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = CSVProcessorConfig(**(config or {}))
        self.settings = get_settings()
        
        # Set default output file if not specified
        if self.config.output_file is None:
            self.config.output_file = self.config.output_dir / "combined.csv"
    
    @property
    def name(self) -> str:
        return "csv_processor"
    
    @property
    def is_available(self) -> bool:
        return True  # Always available as long as pandas is installed
    
    async def initialize(self) -> None:
        """Initialize the CSV processor."""
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def shutdown(self) -> None:
        """Clean up resources."""
        pass
    
    async def find_csv_files(self) -> List[Path]:
        """Find all CSV files in the input directory."""
        if not self.config.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.config.input_dir}")
        
        return fs.find_files(
            directory=self.config.input_dir,
            extensions=["csv"],
            recursive=True
        )
    
    async def read_csv(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Read a single CSV file into a pandas DataFrame."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            df = pd.read_csv(
                file_path,
                delimiter=self.config.delimiter,
                encoding=self.config.encoding
            )
            logger.info(f"Read {len(df)} rows from {file_path.name}")
            return df
        except Exception as e:
            raise CSVProcessingError(f"Error reading {file_path}: {e}")
    
    async def combine_csv_files(
        self,
        file_paths: Optional[List[Union[str, Path]]] = None,
        output_file: Optional[Union[str, Path]] = None
    ) -> Path:
        """Combine multiple CSV files into a single file."""
        if file_paths is None:
            file_paths = await self.find_csv_files()
        
        if not file_paths:
            raise CSVProcessingError("No CSV files found to process")
        
        output_file = Path(output_file) if output_file else self.config.output_file
        
        # Ensure output directory exists and is writable
        output_dir = output_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not fs.is_writable(output_dir):
            # Fall back to a temporary directory if output directory is not writable
            temp_dir = fs.get_temp_dir(prefix="dun_csv_")
            output_file = temp_dir / output_file.name
            logger.warning(f"Output directory not writable, using temporary directory: {output_file}")
        
        try:
            # Read and combine all CSV files
            dfs = []
            for file_path in file_paths:
                try:
                    df = await self.read_csv(file_path)
                    # Add source file column
                    df['_source_file'] = str(file_path)
                    dfs.append(df)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    continue
            
            if not dfs:
                raise CSVProcessingError("No valid CSV data to combine")
            
            # Combine all DataFrames
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Write combined data to output file
            combined_df.to_csv(
                output_file,
                index=False,
                encoding=self.config.encoding,
                sep=self.config.delimiter
            )
            
            logger.info(f"Combined {len(dfs)} files into {output_file} with {len(combined_df)} rows")
            return output_file
            
        except Exception as e:
            raise CSVProcessingError(f"Error combining CSV files: {e}")
    
    async def process_csv_request(self, request: str) -> Dict[str, Any]:
        """Process a natural language request for CSV operations."""
        # This is a simplified version - in a real implementation, you would use an LLM
        # to interpret the request and determine the appropriate CSV operations
        
        # Simple keyword-based processing for demonstration
        request_lower = request.lower()
        
        if "combine" in request_lower or "join" in request_lower:
            output_file = await self.combine_csv_files()
            return {
                "status": "success",
                "message": f"Successfully combined CSV files into {output_file}",
                "output_file": str(output_file)
            }
        elif "list" in request_lower or "show" in request_lower:
            files = await self.find_csv_files()
            return {
                "status": "success",
                "files": [str(f) for f in files],
                "count": len(files)
            }
        else:
            return {
                "status": "error",
                "message": "Could not determine the requested CSV operation"
            }


# Global CSV processor instance
csv_processor = CSVProcessor()
