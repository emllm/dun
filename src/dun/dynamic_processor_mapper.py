import importlib
import inspect
from typing import Optional, List

class DynamicProcessorMapper:
    """
    Automatyczne mapowanie żądania do biblioteki Python i dynamiczna introspekcja jej interfejsu.
    """
    LIBRARY_KEYWORDS = {
        "pandas": ["csv", "dataframe", "excel", "read_csv", "merge", "concat", "join", "plik"],
        "imaplib": ["mail", "imap", "inbox", "email", "fetch", "login", "wiadomość", "skrzynka"],
        "sqlite3": ["database", "sqlite", "query", "table", "insert", "select", "baza"],
        "requests": ["http", "url", "get", "post", "download", "api", "żądanie"],
        # Dodaj więcej bibliotek i słów kluczowych według potrzeb
    }

    def detect_library(self, request: str) -> Optional[str]:
        req = request.lower()
        for lib, keywords in self.LIBRARY_KEYWORDS.items():
            if any(word in req for word in keywords):
                return lib
        return None

    def list_library_functions(self, library: str) -> List[str]:
        try:
            mod = importlib.import_module(library)
            return [name for name, obj in inspect.getmembers(mod) if inspect.isfunction(obj) or inspect.isclass(obj)]
        except Exception:
            return []

    def generate_debug_info(self, request: str) -> str:
        lib = self.detect_library(request)
        if not lib:
            return f"# Nie rozpoznano biblioteki dla żądania: '{request}'"
        functions = self.list_library_functions(lib)
        sample_funcs = functions[:10] if functions else []
        return (
            f"# Rozpoznano bibliotekę: {lib}\n"
            f"# Przykładowe funkcje/klasy: {sample_funcs}\n"
            f"# Możesz wygenerować kod z użyciem tych funkcji lub przekazać do LLM."
        )

    def generate_python_code_stub(self, request: str) -> str:
        lib = self.detect_library(request)
        if not lib:
            return f"# Nie rozpoznano biblioteki dla żądania: '{request}'"
        functions = self.list_library_functions(lib)
        return (
            f"import {lib}\n"
            f"# TODO: Wygeneruj kod na podstawie żądania: '{request}'\n"
            f"# Dostępne funkcje: {functions[:5]}...\n"
        )
