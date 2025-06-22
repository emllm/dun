# Dun - Dynamiczny Uniwersalny Narzędziownik

**D**ynamiczny **U**niwersalny **N**arzędziownik do przetwarzania danych z wykorzystaniem sztucznej inteligencji.

Alternatywnie:
- **D**ata **U**tility **N**etwork - Narzędzie do pracy z danymi i siecią

---

System automatycznego przetwarzania danych z wykorzystaniem LLM (Mistral 7B) do interpretacji żądań w języku naturalnym i dynamicznego instalowania bibliotek Python.

# Dun - Dynamiczny Procesor Danych

> **Note:** Używaj komendy `dun` zamiast `python dun.py` do uruchamiania programu.

## 🚀 Funkcje

- **Interpretacja języka naturalnego**: Przetwarzanie żądań w zwykłym języku polskim
- **Dynamiczne zarządzanie bibliotekami**: Automatyczna instalacja wymaganych pakietów Python
- **Lokalna skrzynka IMAP**: Testowa skrzynka pocztowa z przykładowymi wiadomościami  
- **Integracja z Ollama**: Wykorzystanie modelu Mistral 7B do analizy żądań
- **Organizacja plików**: Automatyczne sortowanie emaili według dat w strukturze folderów

## 📋 Wymagania

- Docker & Docker Compose (opcjonalnie, tylko do uruchomienia z kontenera)
- Python 3.11+
- Poetry (zalecane) lub pip

## 🔧 Instalacja i uruchomienie

### 1. Instalacja z użyciem Poetry (zalecane)

```bash
# Klonowanie repozytorium
git clone <repository>
cd dun

# Instalacja zależności
poetry install

# Aktywacja środowiska wirtualnego
poetry shell

# Utworzenie przykładowych emaili (opcjonalne)
python setup_test_emails.py
```

### 2. Instalacja z użyciem pip

```bash
# Instalacja pakietu
pip install -e .

# lub dla instalacji globalnej
# pip install .
```

### 3. Uruchomienie (tryb interaktywny)

```bash
dun
```

### 4. Uruchomienie z Docker (opcjonalne)

```bash
# Zbuduj i uruchom wszystkie serwisy
docker-compose up --build

# Lub w tle
docker-compose up -d --build
```

### 4. Uruchomienie lokalne (opcjonalnie)

```bash
# Zainstaluj zależności
poetry install

# Uruchom główny skrypt
poetry run python dun.py
```

## ⚙️ Konfiguracja

Konfiguracja aplikacji odbywa się poprzez zmienne środowiskowe. Skopiuj plik `.env.example` do `.env` i dostosuj ustawienia:

```bash
cp .env.example .env
```

### Główne ustawienia

| Zmienna | Wartość domyślna | Opis |
|---------|----------------|-------------|
| `APP_ENV` | `development` | Środowisko działania (development, testing, production) |
| `APP_DEBUG` | `true` | Tryb debugowania (true/false) |
| `LOG_LEVEL` | `INFO` | Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FILE` | `logs/dun.log` | Ścieżka do pliku z logami |

### Konfiguracja IMAP

| Zmienna | Wartość domyślna | Opis |
|---------|----------------|-------------|
| `IMAP_ENABLED` | `true` | Włącza/wyłącza obsługę IMAP |
| `IMAP_SERVER` | `localhost` | Adres serwera IMAP |
| `IMAP_PORT` | `143` | Port serwera IMAP |
| `IMAP_USERNAME` | `testuser@example.com` | Nazwa użytkownika IMAP |
| `IMAP_PASSWORD` | `testpass123` | Hasło IMAP |
| `IMAP_USE_SSL` | `false` | Włącza szyfrowanie SSL |
| `IMAP_FOLDER` | `INBOX` | Domyślny folder pocztowy |
| `IMAP_TIMEOUT` | `30` | Limit czasu połączenia (w sekundach) |
| `IMAP_MARK_AS_READ` | `true` | Oznacz wiadomości jako przeczytane |
| `IMAP_DOWNLOAD_ATTACHMENTS` | `true` | Automatyczne pobieranie załączników |

### Konfiguracja Ollama (LLM)

| Zmienna | Wartość domyślna | Opis |
|---------|----------------|-------------|
| `OLLAMA_ENABLED` | `true` | Włącza/wyłącza integrację z Ollama |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Adres URL serwera Ollama |
| `OLLAMA_MODEL` | `mistral:7b` | Nazwa modelu językowego |
| `OLLAMA_TIMEOUT` | `120` | Limit czasu odpowiedzi (w sekundach) |
| `OLLAMA_MAX_TOKENS` | `2000` | Maksymalna liczba tokenów w odpowiedzi |
| `OLLAMA_TEMPERATURE` | `0.7` | Parametr kreatywności (0-1) |
| `OLLAMA_TOP_P` | `0.9` | Parametr różnorodności odpowiedzi |

### Ścieżki i katalogi

| Zmienna | Wartość domyślna | Opis |
|---------|----------------|-------------|
| `APP_DIR` | `/app` | Główny katalog aplikacji |
| `DATA_DIR` | `./data` | Katalog na dane |
| `OUTPUT_DIR` | `./output` | Katalog wyjściowy |
| `TEMP_DIR` | `./temp` | Katalog tymczasowy |
| `CACHE_DIR` | `./.cache` | Katalog na cache |

### Ustawienia wydajności

| Zmienna | Wartość domyślna | Opis |
|---------|----------------|-------------|
| `MAX_WORKERS` | `4` | Maksymalna liczba wątków roboczych |
| `TASK_TIMEOUT` | `300` | Limit czasu wykonania zadania (w sekundach) |
| `MAX_RETRIES` | `3` | Maksymalna liczba prób ponowienia |
| `RETRY_DELAY` | `5` | Opóźnienie między ponownymi próbami (w sekundach) |

### Bezpieczeństwo

| Zmienna | Wartość domyślna | Opis |
|---------|----------------|-------------|
| `ENABLE_RATE_LIMITING` | `true` | Włącza ograniczanie zapytań |
| `MAX_REQUESTS_PER_MINUTE` | `60` | Maksymalna liczba zapytań na minutę |
| `REQUIRE_AUTH` | `false` | Wymagaj uwierzytelniania |
| `AUTH_TOKEN` | - | Token uwierzytelniający |

## 🏗️ Architektura

```
dun/
├── src/
│   ├── processor_engine.py    # Główny silnik procesora
│   └── llm_analyzer.py        # Analizator LLM
├── docker/
│   ├── dovecot.conf          # Konfiguracja serwera IMAP
│   ├── users                 # Dane użytkowników
│   └── mail/                 # Folder z wiadomościami
├── output/                   # Folder wynikowy
├── dun.py                    # Główny skrypt
├── .env                      # Konfiguracja
└── docker-compose.yml        # Definicja serwisów
```

## 📧 Przykładowe użycie

Po uruchomieniu systemu, procesor automatycznie:

1. **Analizuje żądanie**: 
   ```
   "Pobierz wszystkie wiadomości email ze skrzynki IMAP i zapisz je w folderach 
   uporządkowanych według roku i miesiąca w formacie skrzynka/rok.miesiąc/*.eml"
   ```

2. **Wykrywa wymagane biblioteki**: `imaplib`, `email`

3. **Instaluje biblioteki**: Automatycznie instaluje wymagane pakiety

4. **Łączy się z IMAP**: Wykorzystuje dane z `.env` do połączenia

5. **Pobiera emaile**: Pobiera wszystkie wiadomości ze skrzynki

6. **Organizuje pliki**: Tworzy strukturę folderów:
   ```
   output/
   └── skrzynka/
       ├── 2024.11/
       │   ├── email_1.eml
       │   └── email_2.eml
       ├── 2024.12/
       │   └── email_3.eml
       └── 2025.06/
           ├── email_4.eml
           └── email_5.eml
   ```

## 🔧 Konfiguracja

### Zmienne środowiskowe (.env)

```bash
# Konfiguracja IMAP
IMAP_SERVER=localhost          # Adres serwera IMAP
IMAP_PORT=143                  # Port IMAP
IMAP_USERNAME=testuser@example.com
IMAP_PASSWORD=testpass123
IMAP_USE_SSL=false            # Użycie SSL

# Ścieżki
OUTPUT_DIR=./output           # Folder wyjściowy

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b

# Logowanie
LOG_LEVEL=INFO
```

### Testowa skrzynka IMAP

- **Serwer**: localhost:143
- **Użytkownik**: testuser@example.com  
- **Hasło**: testpass123
- **Protokół**: IMAP bez SSL

## 📝 Przykładowe żądania w języku naturalnym

System rozpoznaje różne typy żądań:

### 1. Pobieranie emaili
```
"Pobierz wszystkie wiadomości email ze skrzynki IMAP i zapisz je w folderach 
uporządkowanych według roku i miesiąca w formacie skrzynka/rok.miesiąc/*.eml"
```

### 2. Filtrowanie po dacie
```
"Pobierz emaile z ostatnich 30 dni i zapisz je w folderze recent_emails"
```

### 3. Filtrowanie po nadawcy
```  
"Pobierz wszystkie emaile od sender@example.com i zapisz je w osobnym folderze"
```

### 4. Analiza załączników
```
"Pobierz emaile z załącznikami i wyodrębnij wszystkie pliki PDF do folderu attachments"
```

## 🔍 Monitorowanie

### Logi systemu
```bash
# Podgląd logów Docker
docker-compose logs -f

# Logi konkretnego serwisu
docker-compose logs -f data-processor
docker-compose logs -f ollama
docker-compose logs -f mailserver
```

### Sprawdzenie statusu Ollama
```bash
curl http://localhost:11434/api/tags
```

### Testowanie IMAP
```bash
# Telnet do serwera IMAP
telnet localhost 143

# Przykładowe komendy IMAP
a1 LOGIN testuser@example.com testpass123
a2 SELECT INBOX
a3 SEARCH ALL
a4 LOGOUT
```

## 🧪 Rozwój i testowanie

### Struktura projektu
```python
# Dodawanie nowego procesora
class CustomProcessor:
    def setup(self):
        # Instaluj biblioteki
        pass
    
    def process(self, data):
        # Logika przetwarzania
        return result
```

### Dodawanie nowych szablonów LLM
```python
# W llm_analyzer.py
def _get_custom_processor(self) -> ProcessorConfig:
    code_template = '''
    # Twój kod tutaj
    result = {"status": "completed"}
    '''
    return ProcessorConfig(...)
```

## 🔧 Rozwiązywanie problemów

### Ollama nie odpowiada
```bash
# Restart Ollama
docker-compose restart ollama

# Sprawdź czy model jest pobrany
docker-compose exec ollama ollama list
```

### IMAP connection refused
```bash
# Sprawdź status serwera pocztowego
docker-compose restart mailserver

# Sprawdź logi
docker-compose logs mailserver
```

### Błędy instalacji pakietów
```bash
# Wyczyść cache pip
docker-compose exec data-processor pip cache purge

# Restart kontenera
docker-compose restart data-processor
```

## 📊 Przykładowy wynik działania

```json
{
    "status": "completed",
    "downloaded_files": [
        "output/skrzynka/2024.11/email_1.eml",
        "output/skrzynka/2024.12/email_2.eml", 
        "output/skrzynka/2025.06/email_3.eml"
    ],
    "total_count": 3,
    "folders_created": [
        "output/skrzynka/2024.11",
        "output/skrzynka/2024.12", 
        "output/skrzynka/2025.06"
    ]
}
```

## 🚀 Rozszerzenia

System może być rozszerzony o:

- **Więcej procesorów**: CSV, JSON, XML, bazy danych
- **Różne protokoły**: POP3, Exchange, SMTP
- **Chmura**: Integracja z Gmail API, Outlook
- **Analiza treści**: NLP, klasyfikacja, sentiment analysis
- **Automatyzacja**: Cron jobs, watchdog, webhooks

## 🧪 Testowanie

Projekt zawiera kompleksowe testy jednostkowe i integracyjne. Aby uruchomić testy:

```bash
# Zainstaluj zależności developerskie
poetry install --with dev

# Uruchom testy
poetry run pytest tests/

# Z pokryciem kodu (wymaga pytest-cov)
poetry run pytest --cov=dun tests/

# Generuj raport HTML z pokryciem
poetry run pytest --cov=dun --cov-report=html tests/
```

### Struktura testów

- `tests/unit/` - Testy jednostkowe poszczególnych komponentów
- `tests/integration/` - Testy integracyjne sprawdzające współdziałanie komponentów
- `tests/conftest.py` - Konfiguracja i wspólne fikstury

## 📄 Licencja

Apache License - zobacz plik LICENSE