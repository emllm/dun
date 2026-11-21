"""Automatyczne mapowanie żądania do biblioteki Python i introspekcja interfejsu."""
from __future__ import annotations

import importlib
import inspect
from typing import Dict, List, Optional

from dun.routing import LexicalRouter, library_router

_ROUTER_TO_MAPPER: Dict[str, str] = {
    "imaplib": "imaplib",
    "sqlalchemy": "sqlite3",
    "requests": "requests",
    "pandas": "pandas",
}

_MAPPER_EXTRA_KEYWORDS: Dict[str, tuple[str, ...]] = {
    "pandas": ("csv", "dataframe", "excel", "read_csv", "merge", "concat", "join"),
    "imaplib": ("mail", "imap", "inbox", "email", "fetch", "login", "wiadomość", "skrzynka"),
    "sqlite3": ("database", "sqlite", "query", "table", "insert", "select", "baza"),
    "requests": ("http", "url", "get", "post", "download", "api"),
}
_FALLBACK_ROUTER = LexicalRouter(
    _MAPPER_EXTRA_KEYWORDS,
    priorities={"imaplib": 4, "sqlite3": 3, "requests": 2, "pandas": 1},
)


class DynamicProcessorMapper:
    """Map natural-language requests to standard/runtime libraries safely."""

    LIBRARY_KEYWORDS = {
        "pandas": ["csv", "dataframe", "excel", "read_csv", "merge", "concat", "join", "plik"],
        "imaplib": ["mail", "imap", "inbox", "email", "fetch", "login", "wiadomość", "skrzynka"],
        "sqlite3": ["database", "sqlite", "query", "table", "insert", "select", "baza"],
        "requests": ["http", "url", "get", "post", "download", "api", "żądanie"],
    }

    def detect_library(self, request: str) -> Optional[str]:
        """Classify ``request`` using token-based lexical routing (no substring traps)."""
        for key, _score in library_router().rank(request):
            mapped = _ROUTER_TO_MAPPER.get(key)
            if mapped is not None:
                return mapped
        return _FALLBACK_ROUTER.best(request, default=None)

    def list_library_functions(self, library: str) -> List[str]:
        """List public functions and classes exposed by ``library``."""
        try:
            mod = importlib.import_module(library)
            return [
                name
                for name, obj in inspect.getmembers(mod)
                if inspect.isfunction(obj) or inspect.isclass(obj)
            ]
        except Exception:
            return []

    def generate_debug_info(self, request: str) -> str:
        """Build human-readable comment block with detected library symbols."""
        lib = self.detect_library(request)
        if not lib:
            return f"# Nie rozpoznano biblioteki dla żądania: '{request}'"
        functions = self.list_library_functions(lib)
        sample_funcs = functions[:10] if functions else []
        return (
            f"# Rozpoznano bibliotekę: {lib}\n"
            f"# Przykładowe funkcje/klasy: {sample_funcs}\n"
            "# Możesz wygenerować kod z użyciem tych funkcji lub przekazać do LLM."
        )

    def generate_python_code_stub(self, request: str) -> str:
        """Build starter code snippet referencing the detected library."""
        lib = self.detect_library(request)
        if not lib:
            return f"# Nie rozpoznano biblioteki dla żądania: '{request}'"
        functions = self.list_library_functions(lib)
        return (
            f"import {lib}\n"
            f"# TODO: Wygeneruj kod na podstawie żądania: '{request}'\n"
            f"# Dostępne funkcje: {functions[:5]}...\n"
        )
