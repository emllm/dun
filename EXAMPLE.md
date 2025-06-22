# Przykłady użycia `dun`

## 1. Tryb interaktywny

Uruchom interaktywną konsolę `dun`:

```bash
dun
```

Po uruchomieniu wprowadź żądanie w języku naturalnym, np.:
```
Pobierz wszystkie wiadomości email ze skrzynki IMAP i zapisz je w folderach 
uporządkowanych według roku i miesiąca w formacie skrzynka/rok.miesiąc/*.eml
```

## 2. Przetwarzanie plików CSV

**Przykładowe żądanie:**
```bash
dun "Przeanalizuj wszystkie pliki CSV w folderze data/, połącz je w jeden dataset"
```

**Opcje dodatkowe:**
- `--output-format json` - format wyjściowy (domyślnie: json)
- `--output-file raport.html` - zapisz wynik do pliku

## 3. Web scraping

**Przykładowe użycie:**
```bash
dun --template web_scraping "Pobierz artykuły z news.com, wyodrębnij tytuły i treść"
```

## 4. Integracja z API

**Przykład:**
```bash
dun "Pobierz dane z REST API, przefiltruj według daty i zapisz do bazy danych PostgreSQL"
```

## 5. Przetwarzanie emaili

**Przykładowe użycie:**
```bash
dun "Sprawdź nowe wiadomości email i zapisz załączniki w folderze ./załączniki"
```

## Konfiguracja

`dun` używa pliku `.env` do konfiguracji. Skopiuj przykładową konfigurację:

```bash
cp env.example .env
```

Następnie edytuj plik `.env` i ustaw odpowiednie wartości konfiguracyjne.

---

## 5. Przetwarzanie obrazów

**Żądanie NLP:**
```
Zmień rozmiar wszystkich zdjęć w folderze images/ na 800x600 i zapisz jako JPEG
```

---

## Użycie

### Generowanie konfiguracji:
```bash
# Tryb interaktywny
python dun.py --interactive

# Z podanym żądaniem
python dun.py "Pobierz emaile z IMAP"

# Z konkretnym szablonem
python dun.py --template email_processing "Pobierz emaile"

# Z walidacją
python dun.py --validate "Pobierz emaile z IMAP"
```

### Uruchamianie zadań:
```bash
# Z wygenerowaną konfiguracją
python enhanced_run.py --config configs/email-processor.yaml

# Tylko walidacja
python enhanced_run.py --config configs/email-processor.yaml --validate-only

# Określone środowisko
python enhanced_run.py --config configs/email-processor.yaml --environment production
```

### Struktura wygenerowanej konfiguracji:
```yaml
apiVersion: dune.io/v1
kind: TaskConfiguration
metadata:
  name: email-imap-processor
  description: "Pobierz wszystkie wiadomości email..."
  version: "1.0"
  created: "2025-06-21T10:00:00Z"
  tags: [email_processing, auto-generated]

task:
  natural_language: "Pobierz wszystkie wiadomości..."
  requirements: [download_emails, organize_files, connect_imap]
  expected_output:
    type: file_structure
    pattern: "output/skrzynka/{year}.{month}/*.eml"

runtime:
  type: docker
  base_image: python:3.11-slim
  python_packages:
    required: [imaplib2, email-validator, python-dotenv, loguru]
    optional: [beautifulsoup4, chardet]
  environment:
    required: [IMAP_SERVER, IMAP_USERNAME, IMAP_PASSWORD]
    optional: [IMAP_PORT, IMAP_USE_SSL, OUTPUT_DIR]

# ... reszta konfiguracji
```