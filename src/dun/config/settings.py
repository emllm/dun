"""Configuration management for the application."""
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

from dotenv import load_dotenv
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from dun.core.protocols import ConfigProtocol


class AppSettings(BaseSettings):
    """Application settings with support for environment variables and .env files."""
    
    # Pydantic v2 model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application settings
    APP_NAME: str = "Dun"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # File system settings
    BASE_DIR: Path = Field(default_factory=Path.cwd)
    DATA_DIR: Path = Field(default_factory=lambda: Path.cwd() / "data")
    LOGS_DIR: Path = Field(default_factory=lambda: Path.cwd() / "logs")
    CACHE_DIR: Path = Field(default_factory=lambda: Path.cwd() / ".cache")
    
    # Ollama settings
    OLLAMA_ENABLED: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 30
    
    # File processing
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list[str] = ["csv", "json", "txt"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    

    @field_validator("BASE_DIR", "DATA_DIR", "LOGS_DIR", "CACHE_DIR", mode="before")
    @classmethod
    def ensure_paths_exist(cls, v: Path) -> Path:
        """Ensure directories exist."""
        if v is None:
            return v
            
        path = Path(v).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if hasattr(self, key):
            setattr(self, key, value)
    
    def load(self) -> None:
        """Load configuration from environment variables."""
        # Pydantic loads from env automatically
        pass
    
    def save(self) -> None:
        """Save configuration to .env file."""
        env_path = Path.cwd() / '.env'
        with open(env_path, 'w') as f:
            for field in self.__fields__:
                if field.isupper() and field != 'CONFIG':
                    value = getattr(self, field)
                    if value is not None:
                        f.write(f"{field}={value}\n")


# Global settings instance
settings = AppSettings()


def get_settings() -> AppSettings:
    """Get the global settings instance."""
    return settings
