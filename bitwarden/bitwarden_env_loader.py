import subprocess
import json
import os
import sys

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.txt')

# Mapowanie: klucz środowiskowy -> szukany wpis w Bitwarden
BW_ENV_MAP = {
    "IMAP_USER": "intranet",
    "IMAP_PASS": "intranet",
    "GMAIL_USER": "gmail",
    "GMAIL_PASS": "gmail",
    "OUTLOOK_USER": "outlook",
    "OUTLOOK_PASS": "outlook",
    "GITHUB_USER": "github",
    "GITHUB_PASS": "github"
}

# Pobierz session_id
with open(SESSION_FILE) as f:
    session_id = f.read().strip()

def get_credentials(domain):
    result = subprocess.run([
        "bw", "list", "items", "--search", domain, "--session", session_id
    ], capture_output=True, text=True)
    items = json.loads(result.stdout)
    if not items:
        return None, None
    item = items[0]
    return item['login']['username'], item['login']['password']

# Ustaw zmienne globalne (os.environ)
for env_user, domain in BW_ENV_MAP.items():
    username, password = get_credentials(domain)
    if env_user.endswith("USER") and username:
        os.environ[env_user] = username
    elif env_user.endswith("PASS") and password:
        os.environ[env_user] = password

# Przykład użycia:
print("IMAP_USER:", os.environ.get("IMAP_USER"))
print("IMAP_PASS:", os.environ.get("IMAP_PASS"))
