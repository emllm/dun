import subprocess
import json
import sys

with open('session.txt') as f:
    session_id = f.read().strip()

SOCIAL_MEDIA_NAMES = ["facebook", "twitter", "linkedin"]

for name in SOCIAL_MEDIA_NAMES:
    result = subprocess.run([
        "bw", "list", "items", "--search", name, "--session", session_id
    ], capture_output=True, text=True)
    items = json.loads(result.stdout)
    if not items:
        print(f"Brak danych dla: {name}")
        continue
    item = items[0]
    print(f"{name.title()} | Login: {item['login']['username']} | Hasło: {item['login']['password']}")
