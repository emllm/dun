# Runy - Dynamiczny Procesor Danych

run LLM procesor on python with dynamic inlcuding and building  pipelines based on imported libraries just based on Natural Command Sentence



System automatycznego przetwarzania danych z wykorzystaniem LLM (Mistral 7B) do interpretacji żądań w języku naturalnym i dynamicznego instalowania bibliotek Python.

## 🚀 Funkcje

- **Interpretacja języka naturalnego**: Przetwarzanie żądań w zwykłym języku polskim
- **Dynamiczne zarządzanie bibliotekami**: Automatyczna instalacja wymaganych pakietów Python
- **Lokalna skrzynka IMAP**: Testowa skrzynka pocztowa z przykładowymi wiadomościami  
- **Integracja z Ollama**: Wykorzystanie modelu Mistral 7B do analizy żądań
- **Organizacja plików**: Automatyczne sortowanie emaili według dat w strukturze folderów

## 📋 Wymagania

- Docker & Docker Compose
- Python 3.11+ (dla lokalnego uruchamiania)
- Poetry (dla lokalnego uruchamiania)

## 🔧 Instalacja i uruchomienie

### 1. Klonowanie i przygotowanie

```bash
git clone <repository>
cd runy
```

### 2. Utworzenie przykładowych emaili

```bash
python setup_test_emails.py
```

### 3. Uruchomienie z Docker

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
poetry run python run.py
```

## 🏗️ Architektura

```
runy/
├── src/
│   ├── processor_engine.py    # Główny silnik procesora
│   └── llm_analyzer.py        # Analizator LLM
├── docker/
│   ├── dovecot.conf          # Konfiguracja serwera IMAP
│   ├── users                 # Dane użytkowników
│   └── mail/                 # Folder z wiadomościami
├── output/                   # Folder wynikowy
├── run.py                    # Główny skrypt
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

3. **Instaluje