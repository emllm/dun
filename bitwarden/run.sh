#!/bin/bash
set -e

# Uruchomienie Vaultwarden z docker-compose
echo "[1/3] Uruchamianie Vaultwarden (docker-compose) na porcie z .env..."
docker-compose --env-file .env up -d

# Sprawdzenie, czy dane zostały załadowane przez populate_bitwarden.py
echo "[2/3] Weryfikacja czy dane zostały załadowane przez populate_bitwarden.py..."
if [ ! -f session.txt ]; then
  echo "Brak pliku session.txt! Zaloguj się przez CLI i odblokuj sejf:"
  echo "  bw config server http://localhost:${PORT:-8082}"
  echo "  bw login $BW_EMAIL $BW_PASSWORD"
  echo "  bw unlock --raw > session.txt"
  exit 1
fi

python3 populate_bitwarden.py

# Pokazanie zawartości sejfu

echo "[3/3] Zawartość sejfu Bitwarden (wszystkie dane):"
SESSION_ID=$(cat session.txt)
bw list items --session "$SESSION_ID" | jq '.'

echo "---"
echo "Jeśli nie widzisz danych, upewnij się że skrypt populate_bitwarden.py działa poprawnie i sejf jest odblokowany."
