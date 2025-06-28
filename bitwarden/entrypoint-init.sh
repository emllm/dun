#!/bin/sh
# Tworzy domyślnego użytkownika w Vaultwarden jeśli nie istnieje
# Używa zmiennych BW_EMAIL i BW_PASSWORD z .env lub wartości domyślnych

EMAIL="${BW_EMAIL:-test@example.com}"
PASSWORD="${BW_PASSWORD:-Test123456789}"
echo "[entrypoint-init] EMAIL=$EMAIL PASSWORD=$PASSWORD"
DATA_DIR="/data"
USERS_JSON="$DATA_DIR/users.json"

if [ ! -f "$USERS_JSON" ] || ! grep -q "$EMAIL" "$USERS_JSON"; then
  echo "[entrypoint-init] Tworzenie użytkownika $EMAIL ..."
  vaultwarden hash_password "$PASSWORD" > /tmp/hashed.txt
  HASH=$(cat /tmp/hashed.txt)
  rm /tmp/hashed.txt
  # Dodaj użytkownika do users.json
  jq --arg email "$EMAIL" --arg hash "$HASH" '.users += [{"email":$email,"password_hash":$hash,"email_verified":true}]' "$USERS_JSON" > "$USERS_JSON.tmp" && mv "$USERS_JSON.tmp" "$USERS_JSON"
else
  echo "[entrypoint-init] Użytkownik $EMAIL już istnieje."
fi
