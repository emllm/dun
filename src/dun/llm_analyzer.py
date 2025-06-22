"""
Analizator LLM do interpretacji żądań w języku naturalnym.
"""

import json
import os
import requests
from typing import Dict, Any
from loguru import logger
from .processor_engine import ProcessorConfig


class LLMAnalyzer:
    """Analizator wykorzystujący LLM do interpretacji żądań."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral:7b"):
        self.base_url = base_url
        self.model = model
        self._check_ollama_connection()

    def _check_ollama_connection(self):
        """Sprawdza połączenie z Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                logger.success("Połączenie z Ollama nawiązane")
            else:
                logger.warning("Ollama niedostępna, używanie domyślnych szablonów")
        except requests.RequestException:
            logger.warning("Nie można połączyć się z Ollama, używanie domyślnych szablonów")

    def analyze_request(self, request: str) -> ProcessorConfig:
        """Analizuje żądanie i zwraca konfigurację procesora."""
        self.last_request = request  # Store the last request for processing

        # Spróbuj użyć LLM jeśli dostępny
        if os.getenv("OLLAMA_ENABLED", "false").lower() == "true":
            try:
                return self._analyze_with_llm(request)
            except Exception as e:
                logger.warning(f"LLM niedostępny ({e}), używanie domyślnego procesora")
        
        # Użyj odpowiedniego domyślnego procesora
        return self._get_default_imap_processor()

    def _analyze_with_llm(self, request: str) -> ProcessorConfig:
        """Analizuje żądanie za pomocą LLM."""

        prompt = f"""
Przeanalizuj poniższe żądanie i zwróć konfigurację procesora danych w formacie JSON.

Żądanie: {request}

Zwróć odpowiedź w następującym formacie JSON (tylko JSON, bez dodatkowych komentarzy):
{{
    "name": "nazwa_procesora",
    "description": "opis działania",  
    "dependencies": ["lista", "wymaganych", "pakietów"],
    "parameters": {{"parametr": "wartość"}},
    "code_template": "kompletny kod Python do wykonania zadania"
}}

Kod powinien:
1. Wykorzystywać zmienne środowiskowe z prefiksem IMAP_ dla połączenia
2. Zapisywać rezultat w zmiennej 'result' 
3. Używać logger.info() do logowania
4. Tworzyć foldery zgodnie z żądaniem
5. Obsługiwać błędy
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        response_text = result.get("response", "")

        # Wyodrębnij JSON z odpowiedzi
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("Nie znaleziono JSON w odpowiedzi LLM")

        json_text = response_text[json_start:json_end]
        config_data = json.loads(json_text)

        return ProcessorConfig(**config_data)

    def _get_default_imap_processor(self) -> ProcessorConfig:
        """Zwraca domyślny procesor jako fallback."""
        
        # Always use CSV processor for now since we're focusing on CSV processing
        return self._get_csv_processor()
        
        # This code is kept for future reference when we want to support multiple processors
        # # Sprawdź czy żądanie dotyczy CSV
        # if any(keyword in self.last_request.lower() for keyword in ['csv', 'plik', 'dane', 'dataset', 'excel']):
        #     return self._get_csv_processor()
            
        # # Domyślnie zwróć procesor IMAP
        # return self._get_imap_processor()
        
    def _get_csv_processor(self) -> ProcessorConfig:
        """Zwraca konfigurację procesora CSV.
        
        Returns:
            ProcessorConfig: Konfiguracja procesora CSV z kodem do wykonania.
        """
        logger.debug("Tworzenie konfiguracji procesora CSV")
        return ProcessorConfig(
            name="csv_processor",
            description="Procesor łączący pliki CSV w jeden zbiór danych",
            dependencies=["pandas"],
            parameters={"input_dir": "data/", "output_file": "output/combined.csv"},
            code_template="""
import os
import sys
import pandas as pd
from pathlib import Path

# Pobierz ścieżki z zmiennych środowiskowych lub użyj domyślnych
logger.info("Inicjalizacja procesora CSV")
input_dir = os.getenv('INPUT_DIR', 'data/')
output_file = os.getenv('OUTPUT_FILE', 'output/combined.csv')
logger.debug(f"INPUT_DIR: {input_dir}")
logger.debug(f"OUTPUT_FILE: {output_file}")
logger.info(f"Bieżący katalog roboczy: {os.getcwd()}")

# Użyj katalogu tymczasowego jeśli nie można zapisać w docelowej lokalizacji
use_temp_dir = False
err_msg = ""
temp_dir = None
original_output_file = output_file

# Sprawdź czy katalog wyjściowy istnieje, jeśli nie to spróbuj go utworzyć
try:
    output_dir = os.path.dirname(output_file) or '.'
    logger.debug(f"Próba utworzenia katalogu: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    logger.debug(f"Utworzono/istnieje katalog: {output_dir}")
    
    # Sprawdź czy mamy uprawnienia do zapisu
    test_file = os.path.join(output_dir, f'.test_write_{os.getpid()}')
    logger.debug(f"Test zapisu do pliku: {test_file}")
    
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    logger.debug("Test uprawnień zakończony powodzeniem")
    
except Exception as e:
    err_msg = str(e)
    logger.warning(f"Błąd podczas sprawdzania uprawnień: {err_msg}")
    use_temp_dir = True

if use_temp_dir:
    # Jeśli nie można zapisać w docelowej lokalizacji, użyj katalogu tymczasowego
    logger.warning(f"Błąd dostępu do katalogu wyjściowego: {err_msg}")
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix='dun_csv_')
    output_file = os.path.join(temp_dir, 'combined.csv')
    logger.warning(f"Używam katalogu tymczasowego: {output_file}")
    logger.info(f"Pełna ścieżka tymczasowa: {os.path.abspath(output_file)}")
    
    # Upewnij się, że katalog tymczasowy istnieje i jest zapisywalny
    try:
        os.makedirs(temp_dir, exist_ok=True)
        test_file = os.path.join(temp_dir, f'.test_write_{os.getpid()}')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.debug("Potwierdzono możliwość zapisu w katalogu tymczasowym")
    except Exception as e:
        logger.error(f"Błąd podczas sprawdzania uprawnień do katalogu tymczasowego: {str(e)}")
        raise

logger.info(f"Szukam plików CSV w katalogu: {input_dir}")

# Znajdź wszystkie pliki CSV w katalogu
logger.info(f"Przeszukiwanie katalogu {input_dir} w poszukiwaniu plików CSV...")
csv_files = []
for ext in ['.csv', '.CSV']:
    pattern = f'*{ext}'
    logger.debug(f"Wyszukiwanie plików z rozszerzeniem: {pattern}")
    files = list(Path(input_dir).rglob(pattern))
    logger.debug(f"Znaleziono {len(files)} plików z rozszerzeniem {ext}")
    csv_files.extend(files)

logger.info(f"Znaleziono łącznie {len(csv_files)} plików CSV")
logger.debug(f"Lista znalezionych plików: {[str(f) for f in csv_files]}")

if not csv_files:
    error_msg = f"Nie znaleziono plików CSV w katalogu {input_dir}"
    logger.error(error_msg)
    raise ValueError(error_msg)

# Wczytaj i połącz wszystkie pliki CSV
logger.info("Rozpoczęcie wczytywania plików CSV...")
dfs = []
for file in csv_files:
    try:
        file_path = str(file)
        logger.info(f"Przetwarzanie pliku: {file_path}")
        logger.debug(f"Pełna ścieżka: {os.path.abspath(file_path)}")
        
        # Sprawdź rozmiar pliku
        file_size = os.path.getsize(file_path)
        logger.debug(f"Rozmiar pliku: {file_size} bajtów")
        
        # Wczytaj plik CSV
        logger.debug("Wczytywanie danych CSV...")
        df = pd.read_csv(file_path, encoding='utf-8', encoding_errors='replace')
        
        # Zaloguj informacje o wczytanych danych
        logger.info(f"  Wczytano {len(df)} wierszy i {len(df.columns)} kolumn")
        logger.debug(f"Nazwy kolumn: {list(df.columns)}")
        if not df.empty:
            sample_data = df.head(2).to_string()
            logger.debug("Przykładowe dane:")
            logger.debug(sample_data)
        
        dfs.append(df)
        logger.debug(f"Dodano dane z pliku {file_path} do listy")
        
    except Exception as e:
        error_msg = f"Błąd podczas przetwarzania pliku {file}: {str(e)}"
        logger.error(error_msg, exc_info=True)  # Zapis pełnego śladu stosu
        continue

if not dfs:
    error_msg = "Nie udało się wczytać żadnych danych z plików CSV"
    logger.error(error_msg)
    raise ValueError(error_msg)

logger.info(f"Przygotowano {len(dfs)} ramek danych do połączenia")
logger.debug(f"Rozmiary ramek: {[len(df) for df in dfs]}")

# Połącz wszystkie ramki danych
try:
    logger.info("Rozpoczęcie łączenia ramek danych...")
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Pomyślnie połączono dane")
    logger.info(f"Łączna liczba wierszy: {len(combined_df)}")
    logger.info(f"Liczba kolumn: {len(combined_df.columns)}")
    logger.debug(f"Nazwy kolumn po połączeniu: {list(combined_df.columns)}")
    
    if not combined_df.empty:
        sample_combined = combined_df.head(2).to_string()
        logger.debug("Przykładowe dane po połączeniu:")
        logger.debug(sample_combined)
    else:
        logger.warning("Połączona ramka danych jest pusta")
    
    # Sprawdź czy są jakieś dane do zapisania
    if combined_df.empty:
        error_msg = "Brak danych do zapisania - połączona ramka danych jest pusta"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Sprawdź czy są jakieś wiersze danych (pomijając nagłówek)
    if len(combined_df) == 0:
        error_msg = "Brak wierszy danych do zapisania"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Sprawdź czy są jakieś kolumny
    if len(combined_df.columns) == 0:
        error_msg = "Brak kolumn w danych do zapisania"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Użyj już ustawionej ścieżki do pliku wyjściowego (może to być katalog tymczasowy)
    if not use_temp_dir:
        output_file = os.path.join(output_dir, 'combined.csv')
    
    logger.info(f"Zapisywanie połączonych danych do pliku: {output_file}")
    logger.debug(f"Pełna ścieżka do pliku: {os.path.abspath(output_file)}")
    logger.debug(f"Czy używam katalogu tymczasowego? {use_temp_dir}")
    
    try:
        # Upewnij się, że katalog docelowy istnieje
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Zapisz dane do pliku CSV
        combined_df.to_csv(output_file, index=False)
        
        # Sprawdź czy plik został utworzony i nie jest pusty
        if not os.path.exists(output_file):
            error_msg = f"Nie udało się utworzyć pliku wyjściowego: {output_file}"
            logger.error(error_msg)
            raise IOError(error_msg)
            
        if os.path.getsize(output_file) == 0:
            error_msg = f"Plik wyjściowy jest pusty: {output_file}"
            logger.error(error_msg)
            raise IOError(error_msg)
            
        logger.success(f"Pomyślnie zapisano dane do pliku: {output_file}")
        logger.debug(f"Rozmiar zapisanego pliku: {os.path.getsize(output_file)} bajtów")
        
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania pliku: {str(e)}")
        raise
    
    # Zwróć informacje o przetworzonych danych
    result = {
        "status": "success",
        "input_files": [str(f) for f in csv_files],
        "output_file": output_file,
        "rows_processed": len(combined_df),
        "columns": list(combined_df.columns),
        "sample_data": combined_df.head(2).to_dict(orient='records') if not combined_df.empty else []
    }
    
except Exception as e:
    logger.error(f"Błąd podczas łączenia i zapisywania danych: {str(e)}")
    raise

# Pokaż podsumowanie
print('')
print('='*50)
print(f'Przetworzono {len(csv_files)} plików CSV')
print(f'Łączna liczba wierszy: {len(combined_df)}')
columns = ", ".join(combined_df.columns)
print(f'Kolumny: {columns}')
print(f'Wynik zapisano w: {output_file}')
print('='*50)
print('')
"""
        )
        
    def _get_imap_processor(self) -> ProcessorConfig:
        """Zwraca domyślny procesor IMAP."""

        code_template = '''
import imaplib
import email
import os
from datetime import datetime
from pathlib import Path

# Pobierz dane połączenia z zmiennych środowiskowych
imap_server = os.getenv("IMAP_SERVER", "localhost")
imap_port = int(os.getenv("IMAP_PORT", "143"))
username = os.getenv("IMAP_USERNAME")
password = os.getenv("IMAP_PASSWORD")
use_ssl = os.getenv("IMAP_USE_SSL", "false").lower() == "true"

if not username or not password:
    raise ValueError("Brak danych logowania IMAP w zmiennych środowiskowych")

logger.info(f"Łączenie z serwerem IMAP: {imap_server}:{imap_port}")

# Nawiąż połączenie
if use_ssl:
    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
else:
    mail = imaplib.IMAP4(imap_server, imap_port)

mail.login(username, password)
mail.select("inbox")

logger.info("Pobieranie listy wiadomości...")

# Pobierz wszystkie wiadomości
result, data = mail.search(None, "ALL")
email_ids = data[0].split()

downloaded_files = []
base_path = Path(output_dir) / "skrzynka"

logger.info(f"Znaleziono {len(email_ids)} wiadomości")

for i, email_id in enumerate(email_ids):
    try:
        # Pobierz wiadomość
        result, msg_data = mail.fetch(email_id, "(RFC822)")
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Pobierz datę wiadomości
        date_header = email_message.get("Date")
        if date_header:
            try:
                date_tuple = email.utils.parsedate_tz(date_header)
                if date_tuple:
                    timestamp = email.utils.mktime_tz(date_tuple)
                    msg_date = datetime.fromtimestamp(timestamp)
                else:
                    msg_date = datetime.now()
            except:
                msg_date = datetime.now()
        else:
            msg_date = datetime.now()

        # Utwórz folder rok.miesiąc
        year_month = f"{msg_date.year}.{msg_date.month:02d}"
        folder_path = base_path / year_month
        folder_path.mkdir(parents=True, exist_ok=True)

        # Zapisz plik .eml
        filename = folder_path / f"email_{email_id.decode()}.eml"
        with open(filename, "wb") as f:
            f.write(email_body)

        downloaded_files.append(str(filename))
        logger.info(f"Zapisano: {filename}")

    except Exception as e:
        logger.error(f"Błąd przetwarzania wiadomości {email_id}: {e}")

mail.close()
mail.logout()

result = {
    "status": "completed",
    "downloaded_files": downloaded_files,
    "total_count": len(downloaded_files),
    "folders_created": list(set([str(Path(f).parent) for f in downloaded_files]))
}

logger.success(f"Pobrano {len(downloaded_files)} wiadomości do {len(result['folders_created'])} folderów")
'''

        return ProcessorConfig(
            name="imap_email_downloader",
            description="Pobiera wiadomości email z IMAP i organizuje je w foldery rok.miesiąc",
            dependencies=["imaplib", "email"],
            parameters={},
            code_template=code_template
        )