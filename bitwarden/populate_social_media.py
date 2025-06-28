import os
import subprocess
import json
from dotenv import load_dotenv

# Wczytaj zmienne z .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SOCIAL_MEDIA = [
    {
        "name": "facebook",
        "login": {
            "username": os.environ.get("FB_USER", "fb_test"),
            "password": os.environ.get("FB_PASS", "fb_pass"),
            "uri": "https://facebook.com"
        }
    },
    {
        "name": "twitter",
        "login": {
            "username": os.environ.get("TW_USER", "tw_test"),
            "password": os.environ.get("TW_PASS", "tw_pass"),
            "uri": "https://twitter.com"
        }
    },
    {
        "name": "linkedin",
        "login": {
            "username": os.environ.get("LN_USER", "ln_test"),
            "password": os.environ.get("LN_PASS", "ln_pass"),
            "uri": "https://linkedin.com"
        }
    }
]

with open('session.txt') as f:
    session_id = f.read().strip()

for entry in SOCIAL_MEDIA:
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
        print(f"Błąd dodawania {entry['name']}: {proc.stderr}")
