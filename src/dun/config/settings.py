"""Configuration management for the application."""
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

from dotenv import load_dotenv
from pydantic import Field, field_validator, ConfigDict
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource

from dun.core.protocols import ConfigProtocol


class EnvSettingsSource(PydanticBaseSettingsSource):
    """Custom settings source that loads from .env file."""
    
    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from environment variables."""
        # Load .env file if it exists
        env_path = Path.cwd() / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        
        # Get the value from environment variables
        env_val = os.environ.get(field_name.upper())
        if env_val is not None:
            return env_val, field_name, False
            
        # Try with the field's alias if it exists
        if field.alias and field.alias != field_name:
            env_val = os.environ.get(field.alias.upper())
            if env_val is not None:
                return env_val, field.alias, False
                
        return None, field_name, False


class AppSettings(BaseSettings, ConfigProtocol):
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
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources with our custom env source."""
        return (EnvSettingsSource(settings_cls),)
    
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
