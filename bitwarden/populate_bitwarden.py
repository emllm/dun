import subprocess
import json
import sys

# Dane do dodania do sejfu
ENTRIES = [
    {
        "name": "intranet",
        "login": {
            "username": "intranet_user",
            "password": "intranet_pass",
            "uri": "https://intranet"
        }
    },
    {
        "name": "gmail",
        "login": {
            "username": "example@gmail.com",
            "password": "gmail_pass",
            "uri": "https://mail.google.com"
        }
    },
    {
        "name": "outlook",
        "login": {
            "username": "outlook_user",
            "password": "outlook_pass",
            "uri": "https://outlook.office.com"
        }
    },
    {
        "name": "github",
        "login": {
            "username": "gh_user",
            "password": "gh_pass",
            "uri": "https://github.com"
        }
    }
]

# Użyj session_id z pliku session.txt
with open('session.txt') as f:
    session_id = f.read().strip()

for entry in ENTRIES:
    item = {
        "type": 1,  # login
        "name": entry["name"],
        "login": entry["login"]
    }
    proc = subprocess.run([
        "bw", "create", "item", "--session", session_id
    ], input=json.dumps(item), capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"Dodano: {entry['name']}")
    else:
        print(f"Błąd dodawania {entry['name']}: {proc.stderr}", file=sys.stderr)
