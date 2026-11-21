"""Environment variable definitions and validation constants for Dun."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

ALLOWED_URL_SCHEMES: tuple[str, ...] = (
    "http://",
    "https://",
    "ftp://",
    "file://",
    "postgresql://",
    "postgres://",
    "mysql://",
    "sqlite://",
    "redis://",
    "rediss://",
    "mongodb://",
    "amqp://",
)


@dataclass
class EnvVariable:
    """Declarative specification for one runtime environment variable."""

    name: str
    description: str
    type: str  # str, int, bool, path, url, email
    required: bool
    default_value: Optional[str] = None
    validation_pattern: Optional[str] = None
    auto_detect_methods: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


def load_env_definitions() -> Dict[str, EnvVariable]:
    """Return built-in environment variable specifications indexed by variable name."""
    return {
        "IMAP_SERVER": EnvVariable(
            name="IMAP_SERVER",
            description="Adres serwera IMAP (np. imap.gmail.com)",
            type="str",
            required=True,
            validation_pattern=r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            auto_detect_methods=["common_providers", "dns_lookup"],
            examples=["imap.gmail.com", "imap.outlook.com", "mail.company.com"],
        ),
        "IMAP_PORT": EnvVariable(
            name="IMAP_PORT",
            description="Port serwera IMAP",
            type="int",
            required=False,
            default_value="993",
            validation_pattern=r"^(143|993|[1-9]\d{1,4})$",
            examples=["143", "993"],
        ),
        "IMAP_USERNAME": EnvVariable(
            name="IMAP_USERNAME",
            description="Nazwa użytkownika IMAP (zazwyczaj email)",
            type="email",
            required=True,
            validation_pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            auto_detect_methods=["git_config", "system_user"],
            examples=["user@gmail.com", "john.doe@company.com"],
        ),
        "IMAP_PASSWORD": EnvVariable(
            name="IMAP_PASSWORD",
            description="Hasło IMAP (lub hasło aplikacji)",
            type="str",
            required=True,
            auto_detect_methods=["keyring", "env_file"],
        ),
        "DATABASE_URL": EnvVariable(
            name="DATABASE_URL",
            description="URL połączenia z bazą danych",
            type="url",
            required=False,
            validation_pattern=r"^(postgresql|postgres|mysql|sqlite|redis|rediss|mongodb|amqp)://.*",
            auto_detect_methods=["docker_compose", "local_services"],
            examples=[
                "postgresql://user:pass@localhost:5432/dbname",
                "sqlite:///data.db",
                "mysql://user:pass@localhost:3306/dbname",
            ],
        ),
        "API_KEY": EnvVariable(
            name="API_KEY",
            description="Klucz API do autoryzacji",
            type="str",
            required=False,
            auto_detect_methods=["env_file", "keyring"],
        ),
        "API_BASE_URL": EnvVariable(
            name="API_BASE_URL",
            description="Bazowy URL API",
            type="url",
            required=False,
            validation_pattern=r"^https?://.*",
            examples=["https://api.example.com", "http://localhost:8000"],
        ),
        "INPUT_DIR": EnvVariable(
            name="INPUT_DIR",
            description="Katalog z plikami wejściowymi",
            type="path",
            required=False,
            default_value="./input",
            auto_detect_methods=["current_directory", "common_paths"],
            examples=["./data", "/home/user/documents"],
        ),
        "OUTPUT_DIR": EnvVariable(
            name="OUTPUT_DIR",
            description="Katalog dla plików wyjściowych",
            type="path",
            required=False,
            default_value="./output",
            auto_detect_methods=["current_directory"],
            examples=["./output", "/tmp/results"],
        ),
        "LOG_LEVEL": EnvVariable(
            name="LOG_LEVEL",
            description="Poziom logowania",
            type="str",
            required=False,
            default_value="INFO",
            validation_pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
            examples=["DEBUG", "INFO", "WARNING", "ERROR"],
        ),
    }
