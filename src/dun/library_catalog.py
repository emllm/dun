"""Built-in library catalogue and task mappings for Dun interactive discovery."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

LIBRARY_PRIORITIES: Dict[str, int] = {
    "IMAP Email Client": 10,
    "SQL Database Access": 9,
    "HTTP Client": 8,
    "Data Analysis": 7,
    "Image Processing": 6,
}


@dataclass
class LibraryInterface:
    """Metadata and parameter schema describing a runtime library."""

    name: str
    package: str
    main_function: str
    required_params: List[str]
    optional_params: List[str]
    param_types: Dict[str, str]
    param_descriptions: Dict[str, str]
    examples: List[Dict[str, Any]]
    cli_interface: Optional[str] = None


@dataclass
class TaskMapping:
    """Association between routing keywords and candidate libraries."""

    task_keywords: List[str]
    libraries: List[LibraryInterface]
    priority: int = 1


def build_library_database() -> Dict[str, LibraryInterface]:
    """Return built-in library metadata indexed by canonical key."""
    return {
        "imaplib": LibraryInterface(
            name="IMAP Email Client",
            package="imaplib",
            main_function="IMAP4_SSL",
            required_params=["server", "username", "password"],
            optional_params=["port", "use_ssl", "folder"],
            param_types={
                "server": "str",
                "username": "str",
                "password": "str",
                "port": "int",
                "use_ssl": "bool",
                "folder": "str",
            },
            param_descriptions={
                "server": "Adres serwera IMAP (np. imap.gmail.com)",
                "username": "Nazwa użytkownika/email",
                "password": "Hasło do skrzynki",
                "port": "Port serwera (143 dla IMAP, 993 dla IMAPS)",
                "use_ssl": "Czy używać szyfrowania SSL",
                "folder": "Folder do przetwarzania (domyślnie INBOX)",
            },
            examples=[
                {
                    "server": "imap.gmail.com",
                    "username": "user@gmail.com",
                    "password": "app_password",
                    "port": 993,
                    "use_ssl": True,
                }
            ],
        ),
        "sqlalchemy": LibraryInterface(
            name="SQL Database Access",
            package="sqlalchemy",
            main_function="create_engine",
            required_params=["database_url"],
            optional_params=["pool_size", "echo", "timeout"],
            param_types={
                "database_url": "str",
                "pool_size": "int",
                "echo": "bool",
                "timeout": "int",
            },
            param_descriptions={
                "database_url": "URL połączenia z bazą danych (postgresql://user:pass@host/db)",
                "pool_size": "Rozmiar puli połączeń",
                "echo": "Czy logować zapytania SQL",
                "timeout": "Timeout połączenia w sekundach",
            },
            examples=[
                {
                    "database_url": "postgresql://user:password@localhost:5432/mydb",
                    "pool_size": 5,
                    "echo": False,
                },
                {"database_url": "sqlite:///data.db"},
            ],
        ),
        "requests": LibraryInterface(
            name="HTTP Client",
            package="requests",
            main_function="get",
            required_params=["url"],
            optional_params=["headers", "timeout", "verify_ssl", "proxies"],
            param_types={
                "url": "str",
                "headers": "dict",
                "timeout": "int",
                "verify_ssl": "bool",
                "proxies": "dict",
            },
            param_descriptions={
                "url": "URL do pobrania",
                "headers": "Nagłówki HTTP (jako słownik)",
                "timeout": "Timeout żądania w sekundach",
                "verify_ssl": "Czy weryfikować certyfikaty SSL",
                "proxies": "Konfiguracja proxy (jako słownik)",
            },
            examples=[
                {
                    "url": "https://api.example.com/data",
                    "headers": {"User-Agent": "Dun Bot 1.0"},
                    "timeout": 30,
                }
            ],
        ),
        "pandas": LibraryInterface(
            name="Data Analysis",
            package="pandas",
            main_function="read_csv",
            required_params=["filepath"],
            optional_params=["separator", "encoding", "header_row"],
            param_types={
                "filepath": "str",
                "separator": "str",
                "encoding": "str",
                "header_row": "int",
            },
            param_descriptions={
                "filepath": "Ścieżka do pliku CSV",
                "separator": "Separator kolumn (domyślnie ',')",
                "encoding": "Kodowanie pliku (np. utf-8, cp1250)",
                "header_row": "Numer wiersza z nagłówkami (0 = pierwszy wiersz)",
            },
            examples=[{"filepath": "data.csv", "separator": ",", "encoding": "utf-8"}],
        ),
        "pillow": LibraryInterface(
            name="Image Processing",
            package="Pillow",
            main_function="Image.open",
            required_params=["image_path"],
            optional_params=["output_format", "quality", "resize_dimensions"],
            param_types={
                "image_path": "str",
                "output_format": "str",
                "quality": "int",
                "resize_dimensions": "tuple",
            },
            param_descriptions={
                "image_path": "Ścieżka do pliku obrazu",
                "output_format": "Format wyjściowy (JPEG, PNG, WEBP)",
                "quality": "Jakość kompresji (1-100 dla JPEG)",
                "resize_dimensions": "Nowe wymiary jako (width, height)",
            },
            examples=[
                {
                    "image_path": "input.jpg",
                    "output_format": "JPEG",
                    "quality": 85,
                    "resize_dimensions": (800, 600),
                }
            ],
        ),
    }


def build_task_mappings(library_database: Dict[str, LibraryInterface]) -> List[TaskMapping]:
    """Return task-keyword to library list mappings."""
    return [
        TaskMapping(
            task_keywords=["email", "imap", "pop3", "skrzynka", "wiadomość", "poczta"],
            libraries=[library_database["imaplib"]],
            priority=1,
        ),
        TaskMapping(
            task_keywords=["baza", "sql", "postgresql", "mysql", "sqlite"],
            libraries=[library_database["sqlalchemy"]],
            priority=1,
        ),
        TaskMapping(
            task_keywords=["http", "api", "rest", "strona", "url", "website"],
            libraries=[library_database["requests"]],
            priority=1,
        ),
        TaskMapping(
            task_keywords=["csv", "excel", "pandas", "dataframe", "tabela", "dane"],
            libraries=[library_database["pandas"]],
            priority=1,
        ),
        TaskMapping(
            task_keywords=["obraz", "zdjęcie", "jpg", "png", "resize", "grafika"],
            libraries=[library_database["pillow"]],
            priority=1,
        ),
    ]
